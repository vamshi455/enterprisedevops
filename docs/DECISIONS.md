# Decisions

Decision log for the Shell data platform CI/CD process. The full context is in [HANDOFF.md](../HANDOFF.md) §5.

## As of 25 Oct 2026

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
| D-09 | CR gate before PROD: approved, in window, CR PR list = manifest (checked by hand, see D-27) | Ties the CR to the exact PRs |
| D-10 | Reuse existing managed identities via OIDC federated credentials; no Azure secrets in GitHub | Admin requirement; identities must be user-assigned |
| D-11 | ~~Per-branch config DB copy~~ **Superseded by D-28** (per-developer DB) | — |
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
| D-22 | UAT defaults (to confirm): QA lead approves UAT; business owner signs off; CR raised during UAT; PROD only after business sign-off; UAT failure = drop and re-cut (§5.7d) | Current UAT practice unknown; standard defaults |
| D-23 | Partial failure: drop the release, re-cut the passing PRs from the latest `prod/*` tag; the cut proves independence; the new build goes through QA again (§5.7c) | Good PRs keep moving without risk |
| D-24 | Rework = new fix PR (same story, `Depends-On: #<old>`); old merged PR is never edited; next release lists both (§5.7c) | Squash-merged PRs are immutable; dependency check enforces it |
| D-25 | Fix forward by default; revert only if the story is abandoned, it breaks DEV, or it blocks another cut; reverts via GitHub Revert + explicit config-row delete script (§5.7c) | Releases only take listed PRs, so bad PRs on main are contained |
| D-26 | Cut guards: preview before cut (blocking), `failed-qa`/`failed-uat` label blocks a PR unless its fix is listed (blocking), ownership/sprint check (warning) (§5.7b) | Human error in picking PRs |
| D-27 | **No ServiceNow integration.** CRs raised and approved by hand; release manager checks the CR before PROD and enters its number in `deploy-prod`; workflow generates the CR text (§5.8) | ServiceNow integration takes too long at Shell |
| D-28 | **One fixed config DB per developer** `sqldb-etlcfg-dev-<alias>` (supersedes D-11). Leased to one branch at a time; refreshed from DEV at story start; incremental deploys on push; reset to a clean DEV copy when the PR merges or closes; nightly: 7-day warning, 14-day reset, roster sync; name guard (§5.4) | Isolation without per-branch create/drop; fixed cost; strictly never stale |
| D-29 | **Feature branches are deleted once merged, no exceptions.** Auto-delete head branches ON; draft PR opened for every new branch so it can be restored; closed-unmerged deleted nightly; stale at 14 days, closed at 21; branch-name ruleset; `release/<id>` deleted after its tag (§5.4) | Only `main` is long-lived; no stale branches |

## Notes on recent decisions

- **D-28 Per-developer config DB (25 Oct 2026).** Options weighed: per-branch DBs (most isolated, but create/drop automation,
  copy waits and cleanup per branch), `main` as the test bed (simplest, but DEV stops predicting QA, every test iteration becomes
  a PR, shared-row collisions, more failed cuts) and one fixed DB per developer (chosen). Cleaning is strict: reset on merge/close,
  reset after 14 days without a push, roster sync nightly. Gate 1 checks the debug run used the author's DB at the PR's commit.
  Also proposed: let a release accept story IDs (`AB#5710`) as well as PR numbers.
- **D-29 Branch deletion mandatory (25 Oct 2026).** Merged branches are deleted automatically; no exceptions, because rework is a
  new PR (D-24) and squash-merged branches have no further use. Draft PRs for every branch make deletion reversible.

- **D-27 No ServiceNow integration (24 Oct 2026).** Integrating ServiceNow with CI/CD takes too long at Shell. CRs are raised and
  approved by hand. Before PROD the release manager checks the CR (approved, in window, same PRs, business sign-off) and starts
  `deploy-prod` with the CR number. The `release` run generates a ready-to-paste CR description. PROD is a separate workflow because
  CR scheduling can take days.
- **D-26 Cut guards (24 Oct 2026).** From real experience of mistyped PR numbers: preview before cut (blocking), failed-QA/UAT label
  blocks a PR unless its fix is listed (blocking), ownership/sprint check (warning only).
- **D-22 to D-25 (24 Oct 2026).** UAT defaults to confirm with the team; partial failure = drop and re-cut the passing PRs, back
  through QA; rework always via a new fix PR that depends on the old one; fix forward by default, revert only when the story is
  abandoned, DEV is broken, or another cut is blocked (config rows need an explicit delete script).

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
