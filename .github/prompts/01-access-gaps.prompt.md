---
name: 01-access-gaps
agent: agent
description: 'Compare the access we need with what exists; produce only the missing items for admins (read-only)'
---
Read-only. Use `environment/ENVIRONMENT_FACTS.md` and the reference list in
`reference/enterprisedevops/docs/access/requests_source.py` (47 items, grouped by who grants them).

For each item, check the live state where you can, for example:
`az role assignment list`, `az identity federated-credential list`, SQL `SELECT name, type FROM sys.database_principals`,
`databricks service-principals list`, `databricks grants get`, `gh api repos/<org>/<repo>/environments`,
`gh api repos/<org>/<repo>/rulesets`. Then mark each item Exists / Missing / Can't check.

Write `environment/ACCESS_GAPS.md` with:
1. A table: ID, owner, what is needed, status, evidence.
2. A **short email to admins with only the Missing items**, grouped by admin (GitHub, Entra, Azure RBAC, SQL,
   Databricks, Azure Boards, ServiceNow, Network), using real resource names. Mark DEV items as needed first.
   Keep it under one page.
3. Blocking items for DEV development, called out at the top.

Do not grant or change anything. Stop and show me the email.
