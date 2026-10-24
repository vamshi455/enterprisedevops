---
name: 00-bootstrap
agent: agent
description: 'Read what is already in devops-cicd, consolidate environment facts, answer the open questions (read-only)'
---
Goal: build one trusted picture of our real environment before we write any code. Read-only: do not change anything.

1. Inventory `PDX_Projects/devops-cicd/`: list every file and folder, and summarise what each one holds
   (earlier discovery output, notes, exports). Do not move, rename or delete anything.
2. Read the always-on instructions (`.github/copilot-instructions.md`). If the reference repo `vamshi455/enterprisedevops`
   is not cloned yet, clone it to `PDX_Projects/devops-cicd/reference/enterprisedevops` (read-only use).
3. From the existing files plus fresh read-only checks, fill `environment/ENVIRONMENT_FACTS.md`. Give one section per
   environment (DEV, QA, UAT, PROD), with a table for each:
   tenant ID, subscription ID/name, resource groups, Data Factory name + git config + integration runtimes,
   config SQL server + database + Entra admin + public/private access, Databricks workspace URL + catalogs +
   SQL warehouses + serverless status, Key Vaults, managed identities (name, client ID, **user- or system-assigned**,
   current role assignments), and private endpoints.
   Also cover GitHub (org, plan, repo(s), Actions policy, existing workflows, rulesets, environments) and
   Azure Boards (org, project, area path, work-item states).
   Useful commands: `az account show`, `az group list`, `az datafactory list/show`, `az sql server list`,
   `az sql db list`, `az identity list`, `az role assignment list --assignee <id> --all`,
   `az network private-endpoint list`, `az databricks workspace list`, `databricks catalogs list`,
   `databricks warehouses list`, `gh api orgs/<org>`, `gh api repos/<org>/<repo>/rulesets`,
   `gh api repos/<org>/<repo>/environments`.
4. Record the source for every value (file path or command + date). Mark anything not found as `UNKNOWN`.
5. Answer OQ-01 … OQ-08 at the top of the file: answer, evidence, confidence.
6. Describe how the **current** team deploys today (existing pipelines, how the SQL config scripts get applied)
   in `environment/CURRENT_PROCESS.md`.
7. Create `STATUS.md` and `DECISIONS.md` if missing. Then stop and show me: the OQ answers, top 5 risks, and what you could not access.
