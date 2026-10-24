# Decisions

Decision log for the Shell data platform CI/CD process. The full context is in [HANDOFF.md](../HANDOFF.md) §5.

## As of 24 Oct 2026

| # | Decision | Reason |
|---|---|---|
| D-01 | Every feature is fully tested on its feature branch; only approved, tested PRs reach `main` | Isolate developers; stop testing on `main` |
| D-02 | Release = list of PRs, cherry-picked by squash commit onto the last `prod/*` tag | Move only what is ready; no per-commit cherry-picks |
| D-03 | Squash merge only; 1 PR = 1 commit = 1 story (`AB#`) | PRs become selectable and traceable |
| D-04 | `main` deploys to DEV only (integration) | DEV is a check after merge, not the first test |
| D-05 | Build once; the same artifact goes QA → UAT → PROD | What QA tested is what reaches PROD |
| D-06 | GitHub + GitHub Actions; approvals via GitHub Environments (qa, uat, prod) | Team already uses GitHub |
| D-07 | Release workflow takes a comma-separated `pr_list` input | Same model as the previous Azure DevOps process |
| D-08 | Azure Boards stories linked by `AB#<id>`; the release moves story states | Stories live in Azure Boards |
| D-09 | ServiceNow CR gate before PROD: approved, in window, CR PR list = manifest | Ties the CR to the exact PRs |
| D-10 | Reuse existing managed identities via OIDC federated credentials; no Azure secrets in GitHub | Admin requirement; identities must be user-assigned |
| D-11 | Per-branch config DB copy `sqldb-etlcfg-ft-<id>` (copy of DEV + branch scripts), dropped on PR close | Config testable on the branch (§5.4) |
| D-12 | Config data as one idempotent MERGE per key; runtime tables never deployed | Clean cherry-picks; protects environment state |
| D-13 | Databricks feature isolation via bundle development mode | Built-in per-developer isolation |
| D-14 | Deploy order: Azure SQL config → Unity Catalog → Databricks → ADF | Dependencies first |
| D-15 | Environment settings in Git (`settings/<env>.json`) fed to ADF, bundle and SQL; secrets in Key Vault; Azure App Configuration rejected | Only reviewed, released changes; no hand edits to PROD (§5.13) |
| D-16 | Known caveats accepted: overlapping PRs, main drifting from PROD, ADF debug not testing triggers or volume | Managed by team habits and QA (§5.15) |
| D-17 | **No approval gate for QA**: the release deploys to QA automatically after the cut. Gates renumbered 0–5 | QA environment is for testing; approvals start at UAT |
| D-18 | Gate 1 checks fixed as the 10 items in §5.3, including ADF API verification that the feature-test run succeeded | Explicit, enforceable definition of a reviewable PR |
| D-19 | GitHub org is on **GitHub Enterprise** (OQ-07 answered) | Environment approvals available for UAT and PROD |
| D-20 | **Developers can cut a release** for their own PRs; not restricted to release managers | Empower developers; the queue prevents collisions |
| D-21 | **Release queue**: one release in progress at a time (cut → PROD tag or dropped); a new cut is refused, not queued; every cut starts from the latest `prod/*` tag (§5.7a) | One QA environment; prevents QA overwrites and PROD going backwards |

## Notes on recent decisions

- **D-20 / D-21 Developer cuts + release queue (24 Oct 2026).** Any developer can cut a release for their own PRs. Only one
  release can be in progress (from cut until tagged in PROD or dropped). A new cut while one is in progress is **refused** with a
  message naming that release; the developer re-runs after it ships or is dropped. Every cut starts from the latest PROD tag.
  Dropping uses a `drop-release` workflow (tag `dropped/<id>`). Rejected alternatives: one shared open release that developers add
  to (more complex), and a QA environment per release (too costly).
- **D-17 update:** with the queue, QA's auto-deploy can no longer overwrite a release under test.

- **D-17 No QA approval gate (24 Oct 2026).** A release deploys to QA automatically right after the cut. Gates are now
  0 Feature test · 1 PR → main · 2 Release cut · 3 UAT (QA sign-off) · 4 ServiceNow CR · 5 PROD. The release queue (D-21)
  keeps a second release from overwriting QA.
- **D-18 Gate 1 checks (24 Oct 2026).** Ten required checks (HANDOFF §5.3), including ADF API verification that the
  `Feature-Test-Run` debug run succeeded, a secrets/hardcoded-values scan, and `Release-Note`, `Depends-On` and `Rollback` lines.
- **D-19 GitHub Enterprise confirmed (24 Oct 2026).** UAT and PROD environment approvals are available.

- **D-15 Environment settings in Git (24 Oct 2026).** Source server names and other environment-specific values differ per
  environment (QA reads the test source, UAT the UAT source) and appear in ADF, the config DB rows and Databricks. One
  `settings/<env>.json` per environment is the single source; the deploy workflow feeds ADF ARM parameters, bundle variables and
  SQLCMD variables from it. Secrets stay in Key Vault. Azure App Configuration was rejected because it allowed unreviewed edits,
  including in PROD, on a previous project.
- **Feature config DB behaviour (24 Oct 2026).** The copy is a snapshot of DEV including watermarks; nothing flows back at merge;
  watermarks may need resetting; copies go stale; feature runs must write to per-branch or per-developer targets (open: OQ-09);
  runtime tables are never in deploy scripts.
- **D-16 Accepted caveats (24 Oct 2026).** Overlapping PRs on the same pipeline conflict when released separately; `main` drifts
  from PROD; ADF debug does not test triggers, the production integration runtime or volume.
