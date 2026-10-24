# Handing this work to the local agent (VS Code + GitHub Copilot)

This repository defines the target architecture for the Shell Data Platform GitHub Actions CI/CD process. The local agent is not inventing a new process; it is validating the real environment, documenting the facts, and implementing against this design.

## Architecture summary to implement

### 1. Platform and repo layout
- One repo with three deployment types:
  - `adf/` — Azure Data Factory
  - `databricks/` — Databricks Asset Bundle
  - `sqlconfig/` — Azure SQL config DB used by metadata-driven ADF pipelines
- Environments: DEV, QA, UAT, PROD.
- Each environment has its own ADF factory, config DB, and Databricks workspace.
- CI/CD runs through GitHub + GitHub Actions.
- Work items are tracked as Azure Boards stories using `AB#<id>` in PRs.
- Production changes require ServiceNow change control.

### 2. Branching and feature testing model
- Developers work on feature branches using names like `feature/AB#<id>-short-desc` or `bugfix/AB#<id>-...`.
- Feature work is tested on the branch before merge.
- Gate 1 for PR to `main`:
  - AB# referenced in the PR
  - CODEOWNERS / tech-lead approval
  - checks pass (`ADF validate`, `bundle validate`, `DACPAC build`)
  - `Feature-Test-Run: <ADF run id>` included in PR body
  - squash merge only (1 PR = 1 commit)
- `main` is not a release branch. It is the integration branch that auto-deploys to DEV only.

### 3. ADF branch strategy
- The DEV factory is connected to GitHub in Git mode.
- Developers debug on their feature branch in ADF Git mode.
- ADF Studio publish is disabled.
- ARM templates are exported in CI with `@microsoft/azure-data-factory-utilities`.
- Deployment uses the ARM from the release branch, not a manual publish from Studio.
- Trigger stop/start and cleanup happen in deployment scripts.

### 4. Azure SQL feature database model
- Each feature branch gets a dedicated config DB copy:
  - `sqldb-etlcfg-ft-<id>`
  - Copy of the DEV config DB plus branch DACPAC and config rows
- The config DB name is passed as an ADF linked-service/pipeline parameter called `configDb`.
- Feature DBs are dropped on PR close and by a nightly sweep.
- Config data is deployed with one idempotent MERGE file per config key.
- Runtime tables such as watermarks and run logs are never deployed to feature DBs.

### 5. Databricks developer workflow
- Developers deploy their branch bundles in dev mode with:
  - `databricks bundle deploy -t dev`
- Development mode uses a per-user prefix and a `dev_<user>` schema.
- The bundle is validated before merge.

### 6. Release model: release = list of PRs
- Release is not a branch of all main. It is a curated list of merged, approved PRs.
- The `release` workflow is `workflow_dispatch` and accepts:
  - `pr_list`
  - `release_id`
  - `change_request`
- It validates that PRs are:
  - merged
  - squash-merged
  - linked to AB#
  - not already in production
- PRs are ordered by merge sequence on `main`.
- Each selected PR is cherry-picked with `-x` onto the release branch from the last `prod/<id>` tag.
- A `releases/<id>/manifest.json` file records the PR list and provenance.
- Build occurs once, then the same artifact is deployed through QA -> UAT -> PROD.

### 7. Release branch, tag, and manifest rules
- `release/<id>` is created by the pipeline only.
- `prod/<id>` is an annotated tag created only after a successful PROD deployment.
- A `release-bot` GitHub App is the only actor allowed to create `release/*` branches and `prod/*` tags.
- `git cherry-pick -x` is required so each release commit preserves provenance back to the original PR squash commit.

### 8. Release gating and approvals
- GitHub Environments:
  - `qa`
  - `uat`
  - `prod`
  - plus extra environments for `dev`, `dev-feature`, and `release-cut`
- Required reviewer approval is enforced at the environment level where supported.
- Release gate sequence:
  1. QA deploy approval
  2. UAT deploy approval
  3. ServiceNow CR gate approval (state approved/scheduled within window; PR list equals manifest)
  4. PROD deploy
- PROD deploy closes the CR and updates work items after successful release.

### 9. Deployment order inside each environment
For every environment, the deployment order is:
1. Azure SQL config
2. Unity Catalog
3. Databricks bundle
4. ADF
   - stop triggers
   - apply ARM
   - cleanup deleted resources
   - start triggers

### 10. ServiceNow change control
- Product changes to PROD are controlled via ServiceNow CR.
- CR must include:
  - Release-Id
  - Release-PRs
  - work items
  - components
  - QA/UAT sign-off references
  - implementation and backout plan
  - window dates
- The pipeline checks the CR before PROD deployment and ensures the CR's PR list matches the manifest exactly.

### 11. Key design constraints
- Federated credentials only work with user-assigned managed identities.
- Required reviewer configuration for private/internal repos may require GitHub Enterprise.
- No GitHub secrets for Azure access; use OIDC + federated credentials.
- Never touch QA/UAT/PROD directly; all changes go through approved workflows.
- Never grant access directly; admins handle roles, federated credentials, SQL users, and Databricks principals.

## The local agent's task

1. In `PDX_Projects/devops-cicd/` (keep everything already there), copy in from this repo:
   - `.github/copilot-instructions.md` → `PDX_Projects/devops-cicd/.github/copilot-instructions.md`
   - `.github/prompts/` → `PDX_Projects/devops-cicd/.github/prompts/`
   - `AGENTS.md` → `PDX_Projects/devops-cicd/AGENTS.md`

   If `devops-cicd/.github/copilot-instructions.md` already exists, append our repo guidance under a heading instead of replacing it.

2. Open `PDX_Projects/devops-cicd` as the VS Code workspace folder. The instructions load automatically.

3. In Copilot Chat choose Agent mode and the Claude model, then run:
   - `/00-bootstrap`
   - `/01-access-gaps`
   - `/02-repo-scaffold`
   - `/03-pr-validation`
   - `/04-feature-env`
   - `/05-deploy-dev`
   - `/06-release`
   - `/07-pilot-story`
   - `/status` any time

4. Review each phase before advancing; do not skip the design constraints or the environment validation steps.

## Required discovery and evidence rules
- Read-only by default. Discovery commands are acceptable:
  - `az ... list/show`
  - `gh api` GET
  - `databricks ... list/get`
  - database `SELECT`
- Ask before any command that creates, changes, or deletes anything in Azure, Databricks, GitHub settings, or a database.
- Capture every fact in `environment/ENVIRONMENT_FACTS.md` with the command/source and date.
- Document missing access and required roles in `environment/ACCESS_GAPS.md`.
- Keep `STATUS.md` and `DECISIONS.md` current.

## Guardrails
- Never touch QA, UAT, or PROD resources directly.
- Never grant access yourself.
- Do not put secrets in files, commits, logs, or chat.
- Use OIDC, environment secrets, or Key Vault references only.
- Prefer official CLIs and pinned action versions.
- If a fact is unknown, say so and ask; do not invent resource names.

## Decision summary the agent must preserve
- Test on the feature branch, not on `main`.
- Use PR-level squash merges and cherry-pick by PR list instead of by commit.
- Deploy Azure SQL config changes before Databricks and ADF in every environment.
- Use release branches and manifest-driven validation for QA/UAT/PROD.
- Require GitHub environments and ServiceNow CR gates for production promotion.
- Restrict release branch and tag creation to the `release-bot` GitHub App.

The agent works read-only until approved, never touches production environments directly, and never grants access itself.
