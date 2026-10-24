---
name: 02-repo-scaffold
agent: agent
description: 'Create the platform repo layout for GitHub Actions using real environment names'
---
Using `ENVIRONMENT_FACTS.md` (real names only; ask if something is UNKNOWN), scaffold the platform repo on a branch
`chore/scaffold` (repo name from DECISIONS.md, default `shell-data-platform`; local path
`PDX_Projects/devops-cicd/shell-data-platform`).

- `adf/`: if the DEV factory is already Git-connected elsewhere, plan the import with me first. Otherwise add
  `package.json` (ADF utilities), `arm-template-parameters-definition.json`, `arm-parameters/{dev,qa,uat,prod}.json`.
  Parameterise the config DB linked service with `dbName`.
- `databricks/`: start from the team's existing bundle if one exists; targets dev (development mode), qa, uat, prod
  (production mode, run_as from facts); add `permissions` granting the factory MI CAN_MANAGE_RUN.
- `sqlconfig/`: SQL project (DACPAC) matching how SQL deploys today (OQ-06). Use `Data/<area>/<KEY>.sql` MERGE
  files, a post-deployment script, and SQLCMD variables for env values. Port the existing scripts; don't invent tables.
- `scripts/release/`: port `build_release.py` from the reference repo and add a GitHub provider
  (`gh api repos/{o}/{r}/pulls/{n}`: merged, merge_commit_sha, base=main, AB# from title/body). Keep the tests passing.
- `.github/CODEOWNERS`, `.github/pull_request_template.md` (AB#, Feature-Test-Run, what changed in each project type),
  and `README.md` (developer workflow in 10 lines).

Run local checks (pytest, `databricks bundle validate -t dev` if authenticated, `dotnet build` of sqlconfig).
Open a PR. Update STATUS.md. Stop for review.
