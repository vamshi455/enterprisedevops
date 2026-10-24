---
name: 04-feature-env
agent: agent
description: 'Per-branch Azure SQL config DB so ADF can be tested on the feature branch, plus cleanup'
---
Build feature-branch testing for the config DB, DEV only.

1. `.github/workflows/feature-env.yml`: on push to `feature/**`, `bugfix/**` when `sqlconfig/**` changes, plus
   `workflow_dispatch`; environment `dev-feature`. Steps: derive `<id>` from `AB#<id>` in the branch name →
   `az sql db copy` DEV config DB → `sqldb-etlcfg-ft-<id>` in the feature elastic pool (tag branch + author) →
   `dotnet build` → `sqlpackage /Action:Publish` to the copy with DEV SQLCMD values → grant the developers group
   db_datawriter on that DB → print the exact ADF debug parameters to use.
2. `.github/workflows/feature-cleanup.yml`: on `pull_request` closed + nightly schedule; drop
   `sqldb-etlcfg-ft-*` DBs whose branch no longer exists or that are older than 14 days.
3. ADF: make sure every pipeline that reads config takes `configDb` (default = DEV DB) and passes it to the
   linked service. List the pipelines changed.
4. `docs/feature-testing.md`: the developer steps (push → wait for DB → ADF debug with `configDb` →
   paste the run id into the PR).

Before running anything that creates a database, show me the plan and ask. Test with one branch, then stop.
