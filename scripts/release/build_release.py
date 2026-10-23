#!/usr/bin/env python3
"""
PR-based release builder ("cherry-pick by PR, never by commit").

Given a comma-separated list of merged Pull Request numbers, this tool:

  1. Resolves every PR to its single squash-merge commit on `main`.
  2. Enforces gates: PR is merged, squash-merged (1 parent), linked to >=1 work item,
     and not already released to production.
  3. Orders PRs by their merge order on main (NOT the order typed by the user),
     which minimises cherry-pick conflicts.
  4. Detects likely missing dependencies: earlier, unreleased, *unselected* PRs that
     touch the same files as a selected PR.
  5. Creates `release/<id>` from the production baseline (latest `prod/*` tag)
     and cherry-picks each PR commit with `-x` (so provenance is recorded).
  6. Writes and commits `releases/<id>/manifest.json` -- the single source of truth
     that the QA, UAT and Prod stages (and the ServiceNow CR) all refer to.

Two PR providers are supported:
  * `ado`  - Azure DevOps REST API (real metadata: status, merge strategy, linked work items)
  * `git`  - offline: parses Azure DevOps default squash messages on main
             ("Merged PR 1234: title" ... "Related work items: #5678").
             Used for local dry-runs and tests.

Exit codes: 0 ok, 1 gate failure, 2 cherry-pick conflict, 3 usage/config error.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path

MERGED_PR_RE = re.compile(r"^Merged PR (\d+):\s*(.*)$", re.MULTILINE)
WORK_ITEM_RE = re.compile(r"(?:Related work items:\s*((?:#\d+[,\s]*)+))|(?:AB#(\d+))")
CHERRY_RE = re.compile(r"\(cherry picked from commit ([0-9a-f]{7,40})\)")


# --------------------------------------------------------------------------- git
def git(*args: str, cwd: str | None = None, check: bool = True) -> str:
    res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and res.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed:\n{res.stderr.strip()}")
    return res.stdout.strip()


class GitError(RuntimeError):
    pass


class GateError(RuntimeError):
    pass


# --------------------------------------------------------------------------- model
@dataclass
class PullRequest:
    id: int
    title: str
    merge_commit: str
    status: str = "completed"
    squash: bool = True
    work_items: list[int] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    main_position: int = -1          # index in main's first-parent history (0 = oldest)
    cherry_sha: str | None = None


# --------------------------------------------------------------------------- providers
class GitLogProvider:
    """Reads PR metadata from Azure DevOps-style squash commit messages on main."""

    def __init__(self, repo: str, main_ref: str):
        self.repo, self.main_ref = repo, main_ref
        self._index = self._scan()

    def _scan(self) -> dict[int, PullRequest]:
        out = git("log", "--first-parent", "--reverse", "--format=%H%x1f%P%x1f%B%x1e",
                  self.main_ref, cwd=self.repo)
        index: dict[int, PullRequest] = {}
        for pos, rec in enumerate(r for r in out.split("\x1e") if r.strip()):
            sha, parents, body = rec.strip().split("\x1f", 2)
            m = MERGED_PR_RE.search(body)
            if not m:
                continue
            wis: list[int] = []
            for grp, ab in WORK_ITEM_RE.findall(body):
                if grp:
                    wis += [int(x) for x in re.findall(r"\d+", grp)]
                if ab:
                    wis.append(int(ab))
            files = git("show", "--name-only", "--format=", sha, cwd=self.repo).splitlines()
            index[int(m.group(1))] = PullRequest(
                id=int(m.group(1)), title=m.group(2).strip(), merge_commit=sha,
                squash=len(parents.split()) == 1, work_items=sorted(set(wis)),
                files=[f for f in files if f], main_position=pos)
        return index

    def get(self, pr_id: int) -> PullRequest:
        if pr_id not in self._index:
            raise GateError(f"PR {pr_id}: not found as a completed merge on {self.main_ref}")
        return self._index[pr_id]

    def all_merged(self) -> list[PullRequest]:
        return sorted(self._index.values(), key=lambda p: p.main_position)


class AdoProvider(GitLogProvider):
    """Azure DevOps REST provider. Uses git for ordering/files, ADO for authoritative status,
    merge strategy and linked work items."""

    def __init__(self, repo: str, main_ref: str, org_url: str, project: str, repo_name: str, pat: str):
        self.org_url, self.project, self.repo_name = org_url.rstrip("/"), project, repo_name
        self._auth = "Basic " + base64.b64encode(f":{pat}".encode()).decode()
        super().__init__(repo, main_ref)

    def _api(self, path: str) -> dict:
        url = f"{self.org_url}/{self.project}/_apis/git/repositories/{self.repo_name}/{path}"
        url += ("&" if "?" in url else "?") + "api-version=7.1"
        req = urllib.request.Request(url, headers={"Authorization": self._auth})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)

    def get(self, pr_id: int) -> PullRequest:
        data = self._api(f"pullrequests/{pr_id}")
        if data.get("status") != "completed":
            raise GateError(f"PR {pr_id}: status is '{data.get('status')}', must be 'completed'")
        if data.get("targetRefName") != "refs/heads/main":
            raise GateError(f"PR {pr_id}: targets {data.get('targetRefName')}, must target main")
        strategy = (data.get("completionOptions") or {}).get("mergeStrategy", "unknown")
        sha = data["lastMergeCommit"]["commitId"]
        wis = [int(w["id"]) for w in self._api(f"pullRequests/{pr_id}/workitems").get("value", [])]
        local = next((p for p in self._index.values() if p.merge_commit == sha), None)
        if local is None:
            raise GateError(f"PR {pr_id}: merge commit {sha[:8]} not on first-parent of {self.main_ref}")
        local.title, local.work_items = data.get("title", local.title), wis
        local.squash = strategy == "squash" and local.squash
        return local


# --------------------------------------------------------------------------- core
def parse_pr_list(raw: str) -> list[int]:
    ids = [int(x) for x in re.split(r"[,\s]+", raw.strip()) if x]
    if not ids:
        raise GateError("PR list is empty")
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise GateError(f"Duplicate PR ids in list: {sorted(dupes)}")
    return ids


def latest_prod_tag(repo: str) -> str | None:
    # Primary key = newest creation date; tie-break (same second) on version-aware tag name.
    tags = git("tag", "--list", "prod/*", "--sort=-v:refname", "--sort=-creatordate", cwd=repo).splitlines()
    return tags[0] if tags else None


def released_commits(repo: str, baseline: str) -> set[str]:
    """Commits from main already in production: either ancestors of baseline or recorded via -x."""
    body = git("log", "--format=%B", baseline, cwd=repo)
    return set(CHERRY_RE.findall(body))


def is_released(repo: str, pr: PullRequest, baseline: str, cherry_set: set[str]) -> bool:
    if any(pr.merge_commit.startswith(c) or c.startswith(pr.merge_commit[:len(c)]) for c in cherry_set):
        return True
    r = subprocess.run(["git", "merge-base", "--is-ancestor", pr.merge_commit, baseline], cwd=repo)
    return r.returncode == 0


def dependency_warnings(selected: list[PullRequest], candidates: list[PullRequest]) -> list[dict]:
    sel_ids = {p.id for p in selected}
    warns = []
    for p in selected:
        for c in candidates:
            if c.id in sel_ids or c.main_position >= p.main_position:
                continue
            overlap = sorted(set(p.files) & set(c.files))
            if overlap:
                warns.append({"pr": p.id, "depends_on_unselected_pr": c.id,
                              "title": c.title, "files": overlap})
    return warns


def build_release(repo: str, pr_list: str, release_id: str, provider, baseline: str | None,
                  strict_deps: bool = False, push: bool = False, dry_run: bool = False) -> dict:
    ids = parse_pr_list(pr_list)
    baseline = baseline or latest_prod_tag(repo)
    if not baseline:
        raise GateError("No prod/* tag found; pass --baseline for the very first release")
    baseline_sha = git("rev-parse", f"{baseline}^{{commit}}", cwd=repo)
    cherry_set = released_commits(repo, baseline_sha)

    # Gates per PR -----------------------------------------------------------
    errors, prs = [], []
    for i in ids:
        try:
            p = provider.get(i)
            if not p.squash:
                raise GateError(f"PR {i}: not squash-merged; one PR must equal one commit on main")
            if not p.work_items:
                raise GateError(f"PR {i}: no linked Azure DevOps work item (story/bug)")
            if is_released(repo, p, baseline_sha, cherry_set):
                raise GateError(f"PR {i}: already in production baseline {baseline}")
            prs.append(p)
        except GateError as e:
            errors.append(str(e))
    if errors:
        raise GateError("Gate failures:\n  - " + "\n  - ".join(errors))

    prs.sort(key=lambda p: p.main_position)
    unreleased = [c for c in provider.all_merged() if not is_released(repo, c, baseline_sha, cherry_set)]
    warns = dependency_warnings(prs, unreleased)
    if warns and strict_deps:
        raise GateError("Possible missing dependencies (strict mode):\n" + json.dumps(warns, indent=2))

    manifest = {
        "release_id": release_id,
        "branch": f"release/{release_id}",
        "baseline": {"ref": baseline, "sha": baseline_sha},
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "created_by": os.environ.get("BUILD_REQUESTEDFOR", os.environ.get("USER", "unknown")),
        "pr_ids": [p.id for p in prs],
        "work_items": sorted({w for p in prs for w in p.work_items}),
        "pull_requests": [],
        "dependency_warnings": warns,
        "servicenow": {"change_request": None, "state": None},
        "promotions": [],
    }
    if dry_run:
        manifest["pull_requests"] = [asdict(p) for p in prs]
        return manifest

    # Cherry-pick -------------------------------------------------------------
    branch = manifest["branch"]
    git("checkout", "-B", branch, baseline_sha, cwd=repo)
    for p in prs:
        r = subprocess.run(["git", "cherry-pick", "-x", p.merge_commit], cwd=repo,
                           capture_output=True, text=True)
        if r.returncode != 0:
            conflicted = git("diff", "--name-only", "--diff-filter=U", cwd=repo, check=False).splitlines()
            git("cherry-pick", "--abort", cwd=repo, check=False)
            suspects = sorted({c.id for c in unreleased
                               if c.id not in manifest["pr_ids"] and c.main_position < p.main_position
                               and set(c.files) & set(conflicted)})
            raise ConflictError(p.id, conflicted, suspects)
        p.cherry_sha = git("rev-parse", "HEAD", cwd=repo)

    manifest["pull_requests"] = [asdict(p) for p in prs]
    mpath = Path(repo, "releases", release_id, "manifest.json")
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(json.dumps(manifest, indent=2) + "\n")
    git("add", str(mpath.relative_to(repo)), cwd=repo)
    git("commit", "-m", f"Release {release_id}: PRs {', '.join(map(str, manifest['pr_ids']))}\n\n"
        f"Work items: {', '.join('#'+str(w) for w in manifest['work_items'])}", cwd=repo)
    if push:
        git("push", "-u", "origin", branch, "--force-with-lease", cwd=repo)
    return manifest


class ConflictError(RuntimeError):
    def __init__(self, pr_id: int, files: list[str], suspects: list[int]):
        self.pr_id, self.files, self.suspects = pr_id, files, suspects
        hint = (f" Likely missing predecessor PR(s): {suspects} -- add them to the list or "
                f"defer PR {pr_id}.") if suspects else ""
        super().__init__(f"Cherry-pick conflict on PR {pr_id} in {files}.{hint}")


def candidates(repo: str, provider, baseline: str | None) -> list[dict]:
    baseline = baseline or latest_prod_tag(repo)
    sha = git("rev-parse", f"{baseline}^{{commit}}", cwd=repo)
    cs = released_commits(repo, sha)
    return [{"pr": p.id, "title": p.title, "work_items": p.work_items, "files": p.files}
            for p in provider.all_merged() if not is_released(repo, p, sha, cs)]


# --------------------------------------------------------------------------- cli
def make_provider(a) -> GitLogProvider:
    if a.provider == "ado":
        pat = os.environ.get("ADO_PAT") or os.environ.get("SYSTEM_ACCESSTOKEN")
        missing = [k for k, v in {"--ado-org": a.ado_org, "--ado-project": a.ado_project,
                                  "--ado-repo": a.ado_repo, "ADO_PAT/SYSTEM_ACCESSTOKEN": pat}.items() if not v]
        if missing:
            print(f"Missing ADO settings: {missing}", file=sys.stderr)
            sys.exit(3)
        return AdoProvider(a.repo, a.main_ref, a.ado_org, a.ado_project, a.ado_repo, pat)
    return GitLogProvider(a.repo, a.main_ref)


def vso(name: str, value: str) -> None:
    if os.environ.get("TF_BUILD"):
        print(f"##vso[task.setvariable variable={name};isOutput=true]{value}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["build", "plan", "candidates"])
    ap.add_argument("--prs", help="Comma-separated PR ids, e.g. '1234,1240,1251'")
    ap.add_argument("--release-id", default=dt.date.today().strftime("R%Y.%m.%d"))
    ap.add_argument("--baseline", help="Prod baseline ref (default: latest prod/* tag)")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--main-ref", default="origin/main")
    ap.add_argument("--provider", choices=["git", "ado"], default="git")
    ap.add_argument("--ado-org"), ap.add_argument("--ado-project"), ap.add_argument("--ado-repo")
    ap.add_argument("--strict-deps", action="store_true", help="Fail on dependency warnings")
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args(argv)

    try:
        prov = make_provider(a)
        if a.command == "candidates":
            print(json.dumps(candidates(a.repo, prov, a.baseline), indent=2))
            return 0
        if not a.prs:
            print("--prs is required", file=sys.stderr)
            return 3
        m = build_release(a.repo, a.prs, a.release_id, prov, a.baseline,
                          strict_deps=a.strict_deps, push=a.push, dry_run=a.command == "plan")
        print(json.dumps(m, indent=2))
        for w in m["dependency_warnings"]:
            print(f"WARNING: PR {w['pr']} shares {w['files']} with unselected earlier PR "
                  f"{w['depends_on_unselected_pr']} ({w['title']})", file=sys.stderr)
            if os.environ.get("TF_BUILD"):
                print(f"##vso[task.logissue type=warning]PR {w['pr']} may depend on PR {w['depends_on_unselected_pr']}")
        vso("releaseBranch", m["branch"])
        vso("releaseId", m["release_id"])
        vso("prIds", ",".join(map(str, m["pr_ids"])))
        return 0
    except ConflictError as e:
        print(f"CONFLICT: {e}", file=sys.stderr)
        return 2
    except (GateError, GitError) as e:
        print(f"GATE FAILED: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
