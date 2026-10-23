# ServiceNow change control

## CR template (Normal change)

```
Short description: Shell Data Platform release R2026.11.01
Description:
  Release-Id:  R2026.11.01
  Release-PRs: 1234, 1240, 1251
  Work items:  AB#5678, AB#5690, AB#5702
  Components:  ADF (pl_ingest_sales), Databricks (job_sales_medallion), UC (V0004)
  QA sign-off: <link>    UAT sign-off: <link>
Implementation plan: Azure DevOps pipeline shell-data-release run <url>, stage PROD
Backout plan: redeploy artifact of prod/R2026.10.15; SQL backout script <link if destructive>
Planned start/end: <window>
```

## Pipeline behaviour

| Step | Call | CR effect |
|---|---|---|
| ChangeGate stage | `cr_gate.py check --cr auto` | finds CR by `Release-Id`, requires approval=approved, state Scheduled/Implement, now within window, `Release-PRs` == manifest |
| PROD preDeploy | `cr_gate.py start` | state → Implement, work note with run link |
| PROD success | `cr_gate.py close --result success` | evidence note, state → Review, close code successful |
| PROD failure | `cr_gate.py close --result failed` | failure note, state unchanged for change manager |

## Native alternative

Microsoft's **ServiceNow Change Management** extension for Azure DevOps can be added as a check on the
`shell-data-prod` environment; it can create the CR and poll until approved. Keep `cr_gate.py check`
anyway — the extension doesn't verify that the CR's PR list matches what is actually being deployed.

## Credentials

Store `SNOW_INSTANCE`, `SNOW_USER`, `snowPassword` (or an OAuth token) in an Azure Key Vault–backed
variable group named `servicenow`, scoped to the release pipeline only.
