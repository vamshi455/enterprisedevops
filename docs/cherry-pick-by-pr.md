# Cherry-pick by PR, not by commit

## Why commit-level cherry-picking breaks

A feature branch typically has 5–20 commits ("wip", "fix typo", "address review"). Picking commits
means someone has to know *which* commits make up a feature, in *which* order, and whether a later
"fix" commit belongs to it. Miss one and QA tests something different from what was reviewed.

## How PR-level works

1. **Squash-merge only** on main → each PR becomes exactly one commit whose message carries the PR
   number and linked work items.
2. The release manager supplies `1234,1240,1251`.
3. `build_release.py`:
   * resolves each PR to its squash commit (via ADO REST),
   * rejects PRs that aren't completed, aren't squash, have no work item, or are already in prod,
   * **sorts them by merge order on main** (typed order is ignored),
   * warns/fails if a selected PR touches files changed by an *earlier unselected* unreleased PR,
   * creates `release/<id>` from the last `prod/*` tag and runs `git cherry-pick -x` per PR,
   * on conflict: aborts cleanly and names the probable missing PR(s),
   * commits `releases/<id>/manifest.json`.
4. Every later stage reads the manifest. The CR must list the same PRs.

```mermaid
%%{init: {"gitGraph": {"rotateCommitLabel": false}} }%%
gitGraph
  commit id: "R1" tag: "prod/R1"
  branch "release/R2"
  checkout main
  commit id: "PR 1234"
  commit id: "PR 1238 (wait)"
  commit id: "PR 1240"
  commit id: "PR 1251"
  checkout "release/R2"
  cherry-pick id: "PR 1234" tag: "PR 1234"
  cherry-pick id: "PR 1240" tag: "PR 1240"
  cherry-pick id: "PR 1251" tag: "PR 1251"
  commit id: "manifest" tag: "prod/R2"
```

PR 1238 stays on main until a later release; it never reaches QA, UAT or PROD by accident.

## Provenance

`-x` appends `(cherry picked from commit <sha>)` to every release commit, so the tool can tell, from
git alone, which main commits are already in production — no external database needed.

## Known limits

* File overlap is a heuristic for dependency; ADF validation of the release branch (Build stage) is
  the real proof that every referenced dataset/linked service exists.
* Long-unreleased PRs increase drift. Keep the `candidates` list short.
