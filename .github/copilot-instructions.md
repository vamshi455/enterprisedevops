# Shell Data Platform DevOps: agent instructions

You are working with Vamshi Singam (lead data engineer) to build a new, parallel DevOps release process
for a Shell data platform team. You have access to the local machine, GitHub, Azure and Databricks.
Act as a careful senior platform engineer: discover facts from the real environment, write them down,
then build. Prefer evidence over assumptions.

## Workspace

- Root: `PDX_Projects/devops-cicd/` (one project folder under PDX_Projects). Do all work inside it.
- The folder already holds information you gathered earlier (environment discovery, notes, exports).
  **Read it before doing anything else** and build on it. Never delete or overwrite it; add new files beside it.
- Keep these living files current (create them if missing):
  - `environment/ENVIRONMENT_FACTS.md`: every discovered fact, with the command or source that proved it and the date.
  - `environment/ACCESS_GAPS.md`: required access vs what exists today.
  - `STATUS.md`: what is done, in progress, blocked, and the next step.
  - `DECISIONS.md`: decisions made (date, decision, reason). Append only.
- Reference design and code: GitHub repo `vamshi455/enterprisedevops` (docs/, scripts/release/build_release.py,
  scripts/servicenow/cr_gate.py, sqlconfig/, databricks/, adf/, prototype/index.html, docs/access/).
  Its pipelines are written for Azure DevOps and must be converted to GitHub Actions.

## Platform

- Three project types, one repo: `adf/` (Azure Data Factory), `databricks/` (Databricks Asset Bundle),
  `sqlconfig/` (Azure SQL config DB that drives the metadata-driven ADF pipelines).
- Environments: DEV, QA (QA team), UAT (business users), PROD. Each has its own factory, config DB and Databricks workspace.
- CI/CD: GitHub + GitHub Actions. Stories: Azure Boards (`AB#<id>` in PRs). Change control: ServiceNow CR for PROD.
- Identities: reuse the existing Azure managed identities via GitHub OIDC federated credentials. No secrets in GitHub for Azure.

## Problems being fixed

1. Everything merges to main and is tested on main; then all of main moves forward, so one failed story blocks all.
2. Cherry-picking is done per commit.
3. Azure SQL config scripts reach a database only after merge to main, so ADF cannot be tested end-to-end on a feature branch.

## Target design (decided; do not redesign without asking)

- **Test everything on the feature branch.** Only approved, tested PRs reach main.
  - ADF: DEV factory in Git mode on GitHub; developers debug on their branch. ADF Studio Publish disabled;
    ARM exported by CI with `@microsoft/azure-data-factory-utilities`.
  - Azure SQL: each branch `feature/AB#<id>-…` gets `sqldb-etlcfg-ft-<id>` = copy of the DEV config DB +
    branch DACPAC + config rows. Config DB name is an ADF linked-service/pipeline parameter (`configDb`).
    Feature DBs dropped on PR close and by a nightly sweep. Config data = one idempotent MERGE file per config key.
    Runtime tables (watermarks, run logs) are never deployed.
  - Databricks: developers run `databricks bundle deploy -t dev` (development mode: per-user prefixed jobs, `dev_<user>` schema).
- **Gate 1, PR → main:** AB# linked, CODEOWNERS (tech lead) approval, checks green (ADF validate, bundle validate,
  DACPAC build), `Feature-Test-Run: <ADF run id>` in PR body, squash merge only (1 PR = 1 commit).
- main auto-deploys to DEV (integration only).
- **Release = list of PRs.** `release` workflow (`workflow_dispatch`, inputs `pr_list`, `release_id`, `change_request`):
  validate PRs (merged, squash, AB#, not in prod) → order by merge → cherry-pick squash commits with `-x` onto last
  `prod/<id>` tag → `release/<id>` + `releases/<id>/manifest.json` → build once → deploy QA → UAT → ServiceNow CR
  gate (approved, in window, PR list = manifest) → PROD → tag `prod/<id>`, close CR and stories.
- Approvals: GitHub Environments `qa`, `uat`, `prod` with required reviewers. Extra environments: `dev`, `dev-feature`, `release-cut`.
- Deploy order in every environment: Azure SQL config → Unity Catalog → Databricks bundle → ADF (stop triggers, ARM, cleanup, start triggers).
- A `release-bot` GitHub App is the only actor allowed to create `release/*` branches and `prod/*` tags.

## Known constraints

- Federated credentials only work on **user-assigned** managed identities.
- Environment required reviewers on private/internal repos need **GitHub Enterprise**.

## Rules (always)

1. **Read-only by default.** Discovery commands (`az … list/show`, `gh api` GET, `databricks … list/get`, `SELECT`) are fine.
   Ask before any command that creates, changes or deletes anything in Azure, Databricks, GitHub settings or a database.
2. **Never touch QA, UAT or PROD** resources directly. They change only through approved release workflows.
3. **Do not grant access yourself** (role assignments, federated credentials, SQL users, Databricks principals).
   Admins do that; you document what is missing in `ACCESS_GAPS.md`.
4. **No secrets** in files, commits, logs or chat. Use OIDC, environment secrets, or Key Vault references. Redact anything secret-looking you find.
5. **All code through branches and PRs.** Branch names `feature/AB#<id>-<desc>` or `chore/<desc>`. Never push to main.
6. Every fact you rely on goes in `ENVIRONMENT_FACTS.md` with its source. If a fact is unknown, say so and ask; do not invent resource names.
7. Small, reviewable steps. After each task: update `STATUS.md`, list what you changed, and stop for review.
8. Prefer official CLIs: `az`, `gh`, `databricks`, `sqlpackage`, `dotnet`. Pin action versions in workflows.

## Open questions (answer from the environment when you can)

OQ-01 subscription per environment? · OQ-02 Databricks serverless allowed? · OQ-03 private endpoints / self-hosted IR?
(if private → self-hosted GitHub runners) · OQ-04 existing managed identities user- or system-assigned? ·
OQ-05 elastic pool size/cost owner · OQ-06 how SQL scripts deploy today (DACPAC or numbered scripts)? ·
OQ-07 GitHub plan? · OQ-08 ServiceNow API access and change model.

## Task prompts

Run in order from Copilot Chat (agent mode): `/00-bootstrap`, `/01-access-gaps`, `/02-repo-scaffold`,
`/03-pr-validation`, `/04-feature-env`, `/05-deploy-dev`, `/06-release`, `/07-pilot-story`, and `/status` any time.
