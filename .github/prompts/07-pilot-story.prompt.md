---
name: 07-pilot-story
agent: agent
description: 'Walk one real story end-to-end through the new process and record the evidence'
---
Pick one small real story with me (ADF change + config row, ideally a Databricks change too). Then:
1. Create `feature/AB#<id>-…`, make the change, push → feature DB created.
2. Guide me through the ADF debug run against `sqldb-etlcfg-ft-<id>`; capture the run id.
3. Open the PR with AB# + Feature-Test-Run; confirm every Gate 1 check; get tech lead review; squash merge.
4. Confirm deploy-dev succeeded and the feature DB was dropped.
5. Run `release` with this PR only, through QA (and UAT if approvers are available).
Record timings, failures and fixes in `pilot/PILOT_REPORT.md`, and list process changes for DECISIONS.md.
