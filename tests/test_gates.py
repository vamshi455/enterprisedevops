import datetime as dt
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "servicenow"))
sys.path.insert(0, str(ROOT / "scripts" / "sql"))
import apply_migrations as am  # noqa: E402
import cr_gate  # noqa: E402

MANIFEST = {"release_id": "R1", "pr_ids": [1240, 1234]}
NOW = dt.datetime(2026, 11, 1, 3, 0, 0)


def cr(**over):
    base = {"approval": "approved", "state": "-2", "start_date": "2026-11-01 02:00:00",
            "end_date": "2026-11-01 06:00:00", "description": "Deploy\nRelease-PRs: 1234, 1240\n"}
    base.update(over)
    return base


def test_cr_passes():
    assert cr_gate.evaluate(cr(), MANIFEST, NOW) == []


@pytest.mark.parametrize("over,needle", [
    ({"approval": "requested"}, "approval"),
    ({"state": "-3"}, "Authorize"),
    ({"start_date": "2026-11-02 02:00:00", "end_date": "2026-11-02 06:00:00"}, "window"),
    ({"description": "Release-PRs: 1234"}, "!= release manifest"),
])
def test_cr_fails(over, needle):
    fails = cr_gate.evaluate(cr(**over), MANIFEST, NOW)
    assert any(needle in f for f in fails)


def test_migrations_load_and_substitute():
    migs = am.load(str(ROOT / "sql/unity-catalog/migrations"), {"catalog": "qa_shell_data", "env": "qa"})
    assert migs[0]["file"].startswith("V0001")
    assert all("${catalog}" not in s for m in migs for s in m["statements"])
    assert migs[-1]["repeatable"]


def test_modified_applied_migration_fails():
    migs = [{"file": "V0001__a.sql", "repeatable": False, "checksum": "new"}]
    with pytest.raises(SystemExit):
        am.plan(migs, {"V0001__a.sql": "old"})


def test_repeatable_reapplied_on_change():
    migs = [{"file": "R__v.sql", "repeatable": True, "checksum": "new"}]
    assert am.plan(migs, {"R__v.sql": "old"}) == migs
