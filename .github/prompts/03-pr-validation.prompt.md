---
name: 03-pr-validation
agent: agent
description: 'Build the Gate 1 workflow that runs on every PR to main'
---
Create `.github/workflows/pr-validation.yml` (on `pull_request` to main), with jobs:
1. `story-link`: fail unless the PR title or body contains `AB#<digits>`.
2. `feature-test-evidence`: fail unless the body has `Feature-Test-Run: <id>`. Skip when the PR changes only docs.
3. `adf-validate`: `npm run build validate` against the DEV factory (OIDC via `azure/login` using the CI identity,
   permissions `id-token: write`, `contents: read`).
4. `bundle-validate`: `databricks bundle validate -t dev` (Databricks CLI with azure-cli auth after `azure/login`).
5. `sql-build`: `dotnet build sqlconfig` → DACPAC artifact.
6. `unit-tests`: pytest for scripts/.
Use path filters so each job only runs when its folder changed, plus one final `pr-validation` job that aggregates
the results. That job is the required status check.
Pin action versions. No secrets. Document the required ruleset settings in `docs/branch-protection.md`
(I will ask the GitHub admin to apply them). Open a PR; stop for review.
