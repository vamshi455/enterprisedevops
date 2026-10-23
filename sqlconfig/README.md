# Azure SQL ETL configuration database

The standalone Azure SQL DB that drives the metadata-driven ADF pipelines (sources, mappings,
parallelism, flags). It is versioned and promoted **with the PR that needs it**, like any other code.

| Kind | Where | Deployed how |
|---|---|---|
| Schema (tables, procs, views) | `Tables/`, `Procs/` | DACPAC (`dotnet build` → `sqlpackage /Action:Publish`) |
| Config data (rows ADF reads) | `Data/<area>/<KEY>.sql`, one `MERGE` per key | post-deployment script, idempotent, env values via SQLCMD variables |
| Runtime state (watermarks, run logs) | schema only | **never** deployed; rows belong to the environment |

## Feature-branch testing (the change)

Before: config scripts reached the DEV DB only after merge to `main`, so ADF changes that need new
config could only be tested *after* merging.

Now: `pipelines/feature-env.yml` gives each feature branch its own database
`sqldb-etlcfg-ft-<workitem>`: a copy of the DEV config DB (= everything already on main) with the
branch's DACPAC + config data deployed on top. Developers debug ADF in Git mode with pipeline
parameter `configDb = sqldb-etlcfg-ft-<workitem>`. Nothing shared changes until the PR is approved.

* Feature DBs live in a small elastic pool; a nightly job drops DBs whose branch is gone or that are > 14 days old.
* ADF linked service `ls_sql_etlconfig` is parameterised by database name; QA/UAT/PROD set it via ARM parameters.
* Keep one config key per file, so cherry-picking PRs doesn't conflict.
