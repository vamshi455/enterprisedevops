#!/usr/bin/env python3
"""
Versioned, idempotent Unity Catalog SQL migrations (Flyway-style, no extra tooling).

  sql/unity-catalog/migrations/V0001__create_schemas.sql
  sql/unity-catalog/migrations/V0002__create_sales_bronze.sql
  sql/unity-catalog/migrations/R__vw_sales_summary.sql   (repeatable: re-applied when checksum changes)

Scripts use ${catalog} / ${env} placeholders so the SAME file runs in dev/qa/uat/prod.
Applied versions + checksums are tracked in ${catalog}.ops.schema_migrations.
A changed checksum on an already-applied V-script fails the deployment (never edit history;
add a new version instead).

Runs against a Databricks SQL Warehouse using databricks-sql-connector.
Env: DATABRICKS_HOST, DATABRICKS_TOKEN (or Azure AD token), DATABRICKS_WAREHOUSE_HTTP_PATH
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^(V(\d+)|R)__([\w\-]+)\.sql$")


def load(dirpath: str, params: dict) -> list[dict]:
    out = []
    for f in sorted(Path(dirpath).glob("*.sql")):
        m = NAME_RE.match(f.name)
        if not m:
            raise SystemExit(f"Bad migration filename: {f.name} (expected V0001__name.sql or R__name.sql)")
        raw = f.read_text()
        sql = raw
        for k, v in params.items():
            sql = sql.replace("${" + k + "}", v)
        out.append({"file": f.name, "repeatable": m.group(1) == "R",
                    "version": int(m.group(2)) if m.group(2) else None,
                    "checksum": hashlib.sha256(raw.encode()).hexdigest(),
                    "statements": [s.strip() for s in sql.split(";") if s.strip()]})
    versions = [m["version"] for m in out if m["version"] is not None]
    if len(versions) != len(set(versions)):
        raise SystemExit("Duplicate migration version numbers")
    return sorted(out, key=lambda m: (m["repeatable"], m["version"] or 0, m["file"]))


def plan(migrations: list[dict], applied: dict[str, str]) -> list[dict]:
    todo = []
    for m in migrations:
        prev = applied.get(m["file"])
        if prev is None or (m["repeatable"] and prev != m["checksum"]):
            todo.append(m)
        elif not m["repeatable"] and prev != m["checksum"]:
            raise SystemExit(f"{m['file']} was modified after being applied. Create a new version instead.")
    return todo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True, choices=["dev", "qa", "uat", "prod"])
    ap.add_argument("--catalog", help="default: <env>_shell_data")
    ap.add_argument("--dir", default="sql/unity-catalog/migrations")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    catalog = a.catalog or f"{a.env}_shell_data"
    migs = load(a.dir, {"catalog": catalog, "env": a.env})

    if a.dry_run:
        for m in migs:
            print(f"[plan] {m['file']} ({len(m['statements'])} statements)")
        return 0

    from databricks import sql as dbsql  # pip install databricks-sql-connector
    with dbsql.connect(server_hostname=os.environ["DATABRICKS_HOST"].replace("https://", ""),
                       http_path=os.environ["DATABRICKS_WAREHOUSE_HTTP_PATH"],
                       access_token=os.environ["DATABRICKS_TOKEN"]) as conn, conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {catalog}.ops")
        cur.execute(f"""CREATE TABLE IF NOT EXISTS {catalog}.ops.schema_migrations (
            file STRING, checksum STRING, applied_at TIMESTAMP, applied_by STRING, release_id STRING)""")
        cur.execute(f"SELECT file, checksum FROM {catalog}.ops.schema_migrations "
                    f"QUALIFY row_number() OVER (PARTITION BY file ORDER BY applied_at DESC) = 1")
        applied = {r[0]: r[1] for r in cur.fetchall()}
        for m in plan(migs, applied):
            print(f"Applying {m['file']}")
            for stmt in m["statements"]:
                cur.execute(stmt)
            cur.execute(f"INSERT INTO {catalog}.ops.schema_migrations VALUES (?, ?, current_timestamp(), ?, ?)",
                        [m["file"], m["checksum"], os.environ.get("BUILD_REQUESTEDFOR", "local"),
                         os.environ.get("RELEASE_ID", "adhoc")])
    return 0


if __name__ == "__main__":
    sys.exit(main())
