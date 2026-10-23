"""End-to-end tests for PR-based cherry-picking against a real temporary git repo."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "release"))
import build_release as br  # noqa: E402


def sh(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def squash_pr(repo, pr_id, title, files: dict, work_item=None):
    for name, content in files.items():
        p = Path(repo, name)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        sh(repo, "add", name)
    msg = f"Merged PR {pr_id}: {title}\n\n"
    if work_item:
        msg += f"Related work items: #{work_item}"
    sh(repo, "commit", "-m", msg)


@pytest.fixture
def repo(tmp_path):
    r = str(tmp_path)
    sh(r, "init", "-b", "main")
    sh(r, "config", "user.email", "ci@example.com")
    sh(r, "config", "user.name", "CI")
    Path(r, "README.md").write_text("base\n")
    sh(r, "add", ".")
    sh(r, "commit", "-m", "initial")
    sh(r, "tag", "prod/R0")
    # PR 101: new ADF pipeline
    squash_pr(r, 101, "Add pl_ingest_sales", {"adf/pipeline/pl_ingest_sales.json": '{"v":1}\n'}, 9001)
    # PR 102: unrelated Databricks notebook
    squash_pr(r, 102, "Add nb_customer_silver", {"databricks/src/notebooks/nb_customer_silver.py": "print(1)\n"}, 9002)
    # PR 103: modifies pl_ingest_sales (depends on 101)
    squash_pr(r, 103, "Tune pl_ingest_sales", {"adf/pipeline/pl_ingest_sales.json": '{"v":2}\n'}, 9003)
    # PR 104: no work item
    squash_pr(r, 104, "Quick fix without story", {"sql/x.sql": "select 1;\n"})
    return r


def prov(repo):
    return br.GitLogProvider(repo, "main")


def test_orders_by_main_and_creates_manifest(repo):
    m = br.build_release(repo, "102, 101", "R1", prov(repo), None)
    assert m["pr_ids"] == [101, 102]                      # merge order, not typed order
    assert m["work_items"] == [9001, 9002]
    assert sh(repo, "rev-parse", "--abbrev-ref", "HEAD") == "release/R1"
    manifest = json.loads(Path(repo, "releases/R1/manifest.json").read_text())
    assert manifest["baseline"]["ref"] == "prod/R0"
    assert not Path(repo, "adf/pipeline/pl_ingest_sales.json").read_text().startswith('{"v":2')


def test_missing_work_item_blocks(repo):
    with pytest.raises(br.GateError, match="no linked Azure DevOps work item"):
        br.build_release(repo, "104", "R1", prov(repo), None, dry_run=True)


def test_unknown_pr_blocks(repo):
    with pytest.raises(br.GateError, match="not found"):
        br.build_release(repo, "999", "R1", prov(repo), None, dry_run=True)


def test_missing_dependency_conflict_names_suspect(repo):
    with pytest.raises(br.ConflictError) as e:
        br.build_release(repo, "103", "R1", prov(repo), None)
    assert e.value.pr_id == 103 and e.value.suspects == [101]
    assert sh(repo, "status", "--porcelain") == ""        # cherry-pick aborted cleanly


def test_dependency_warning_in_plan(repo):
    m = br.build_release(repo, "103", "R1", prov(repo), None, dry_run=True)
    assert m["dependency_warnings"][0]["depends_on_unselected_pr"] == 101


def test_strict_deps_fails_fast(repo):
    with pytest.raises(br.GateError, match="missing dependencies"):
        br.build_release(repo, "103", "R1", prov(repo), None, strict_deps=True, dry_run=True)


def test_already_released_pr_is_rejected_next_time(repo):
    br.build_release(repo, "101,102", "R1", prov(repo), None)
    sh(repo, "tag", "prod/R1")                            # prod deploy tags the release branch
    sh(repo, "checkout", "main")
    with pytest.raises(br.GateError, match="already in production"):
        br.build_release(repo, "101,103", "R2", prov(repo), None, dry_run=True)
    m = br.build_release(repo, "103", "R2", prov(repo), None)   # 101 now in baseline -> no conflict
    assert m["baseline"]["ref"] == "prod/R1" and m["pr_ids"] == [103]


def test_candidates_lists_unreleased(repo):
    br.build_release(repo, "101", "R1", prov(repo), None)
    sh(repo, "tag", "prod/R1")
    sh(repo, "checkout", "main")
    assert [c["pr"] for c in br.candidates(repo, prov(repo), None)] == [102, 103, 104]


def test_duplicate_ids(repo):
    with pytest.raises(br.GateError, match="Duplicate"):
        br.parse_pr_list("1,2,1")
