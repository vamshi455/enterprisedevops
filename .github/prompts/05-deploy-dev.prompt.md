---
name: 05-deploy-dev
agent: agent
description: 'Deploy main to DEV on every merge'
---
Create `.github/workflows/deploy-dev.yml`: on push to main (ignore docs/**), environment `dev`, OIDC with the DEV
deploy identity. Order: (1) Azure SQL config DACPAC publish to the DEV DB, (2) Unity Catalog SQL steps if any,
(3) `databricks bundle deploy -t dev` in production-style mode under the shared root, (4) ADF: export ARM →
pre-deployment script (stop triggers) → `azure/arm-deploy` with `arm-parameters/dev.json` → post-deployment
(cleanup + start triggers).
Make it a reusable workflow `deploy-env.yml` (`workflow_call` with input `env`) so QA/UAT/PROD reuse the same steps.
Dry-run with `--what-if` where possible. Open a PR; stop for review.
