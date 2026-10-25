import sys, re
sys.path.insert(0, 'docs/access')
from requests_source import R, OPEN, GRANTORS
body = open('handoff/handoff_body.md').read()
out = [body]

# 5.12 access table
envmap = dict(zip("DQUP", ["DEV","QA","UAT","PROD"]))
cur = None
for k, name in GRANTORS.items():
    rows = [r for r in R if r[2] == k]
    if not rows: continue
    out.append(f"\n**{name}**\n\n| ID | Principal / target | Env | Permission / action | Why | Phase |\n|---|---|---|---|---|---|")
    for r in rows:
        env = ", ".join(envmap[e] for e in r[4].split(",")) if r[4] else "—"
        perm = r[5] + (f" _(Note: {r[8]})_" if r[8] else "")
        cells = [r[0], r[3], env, perm, r[6], r[7]]
        out.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")

out.append("""
### 5.13 Environment-specific settings (decided: Git is the source of truth)

- One file per environment: `settings/dev.json`, `settings/qa.json`, `settings/uat.json`, `settings/prod.json`, all with
  **the same keys**. Example keys: `sourceServers.<system>`, `landingStorageAccount`, `databricksHost`, `ucCatalog`,
  `keyVaultName`, `selfHostedIrName`, `configSqlServer`, `configDb`.
- The deploy workflow reads `settings/<env>.json` and feeds the same values to all three project types:
  - **ADF:** rendered into ARM parameter overrides (linked service servers/URLs, global parameters).
  - **Databricks:** bundle variables (`databricks bundle deploy -t <env> --var key=value`, or a generated variables file).
  - **Azure SQL config:** SQLCMD variables (`/v:Key=value`) used by the MERGE scripts, e.g. source server names per environment.
- **Secrets never go in settings files.** They stay in Key Vault: ADF linked services use Key Vault references; Databricks uses a
  Key Vault-backed secret scope. Settings files hold only names and URLs.
- Every change goes through a PR and ships with a release. A PR check fails if the four files don't have identical keys.
  CODEOWNERS puts `settings/prod.json` under the release managers.
- **Azure App Configuration was considered and rejected.** It lets people edit values, including PROD, in the portal outside
  review and outside any release; that caused problems in a previous project. Revisit only if values must be shared with other
  tools at runtime, and then only as a read-only copy written by the pipeline from Git.

### 5.14 Decision record (as of 24 Oct 2026)

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
| D-22 | UAT defaults (to confirm): QA lead approves UAT; business owner signs off; CR raised during UAT; PROD only after business sign-off; UAT failure = drop and re-cut (§5.7d) | Current UAT practice unknown; standard defaults |
| D-23 | Partial failure: drop the release, re-cut the passing PRs from the latest `prod/*` tag; the cut proves independence; the new build goes through QA again (§5.7c) | Good PRs keep moving without risk |
| D-24 | Rework = new fix PR (same story, `Depends-On: #<old>`); old merged PR is never edited; next release lists both (§5.7c) | Squash-merged PRs are immutable; dependency check enforces it |
| D-25 | Fix forward by default; revert only if the story is abandoned, it breaks DEV, or it blocks another cut; reverts via GitHub Revert + explicit config-row delete script (§5.7c) | Releases only take listed PRs, so bad PRs on main are contained |
| D-26 | Cut guards: preview before cut (blocking), `failed-qa`/`failed-uat` label blocks a PR unless its fix is listed (blocking), ownership/sprint check (warning) (§5.7b) | Human error in picking PRs |
| D-27 | **No ServiceNow integration.** CRs raised and approved by hand; release manager checks the CR before PROD and enters its number in `deploy-prod`; workflow generates the CR text (§5.8) | ServiceNow integration takes too long at Shell |

### 5.15 Things that are easy to get wrong

- Federated credentials are **not supported on system-assigned managed identities**. If the identities the team wants to reuse
  are system-assigned (e.g. a factory's own identity), new user-assigned identities are needed (max 20 federated credentials each).
- GitHub Environment required reviewers on private/internal repos need GitHub Enterprise. **Confirmed: the org is on GitHub Enterprise**, so the UAT and PROD approvals work.
- **QA has no approval gate.** A release deploys to QA immediately after its cut. The release queue (§5.7a) guarantees only one release is in QA at a time, so a release under test is never overwritten. A developer whose cut is refused must wait until the in-progress release ships or is dropped.
- If SQL/Databricks/ADF use private endpoints, GitHub-hosted runners cannot reach them. Use self-hosted runners in the VNet
  (or GitHub-hosted runners with Azure private networking).
- ADF ARM deployments are incremental: deleted objects stay until the post-deployment script removes them.
- Never edit a released `V`-style schema script or a config MERGE to *remove* rows silently. Add a new change that does it explicitly.
- **Overlapping PRs on the same file.** If two PRs change the same ADF pipeline (or the same config key) and only the later one
  is released, the cherry-pick conflicts. The release tool catches it and names the missing PR, but the team should keep to one
  story per pipeline at a time and release dependent PRs together.
- **main drifts from PROD.** Unreleased PRs accumulate on `main`, so DEV and every feature copy contain work that is not in PROD
  yet. Review the `candidates` list (unreleased PRs) at every release planning and keep it short.
- **ADF debug proves logic, not operations.** Debug runs do not exercise triggers, and they use the DEV integration runtime and
  DEV data. Scheduling, volume and performance are first proven in QA.
- **Feature copies:** reset watermarks to test real loads, refresh stale copies, and never let feature runs write to shared DEV
  targets (§5.4).

---

## 6. Open questions (answer in Phase 2 from evidence)
""")
out.append("| ID | Question | What it affects | Who can answer |\n|---|---|---|---|")
for q in [q for q in OPEN if q[0] not in ("OQ-07","OQ-08")] + [("OQ-07","GitHub plan","ANSWERED 24 Oct 2026: GitHub Enterprise","Vamshi"),("OQ-08","ServiceNow API access","ANSWERED 24 Oct 2026: no integration; CRs are manual (D-27)","Vamshi"),("OQ-10","How does UAT work today: who signs off, when is the CR raised, what happens on failure?","Confirms D-22","Existing team"),("OQ-09","Where do feature (debug) runs write their data today? Do developers share DEV lake paths/tables, or is there a per-developer target?","Output isolation for feature testing (§5.4)","Existing team")]:
    out.append("| " + " | ".join(q) + " |")

def code(path, lang):
    return f"\n```{lang}\n" + open(path).read().rstrip() + "\n```\n"

out.append("""
---

## Appendix A: `scripts/release/build_release.py` (reference implementation, tested)

Port this as-is, then add the GitHub provider (§5.7) and switch CI output from `##vso` to `$GITHUB_OUTPUT`.
""" + code('scripts/release/build_release.py', 'python'))
out.append("""
## Appendix B: `tests/test_build_release.py` (real temporary git repo scenarios)

The tests use Azure DevOps-style squash messages (`Merged PR 101: …`). Add equivalent tests for GitHub-style squash
titles (`<title> (#101)`) and a mocked GitHub API provider.
""" + code('tests/test_build_release.py', 'python'))
out.append("""
## Appendix C: `scripts/servicenow/cr_gate.py` (for later; NOT used now, see D-27)
""" + code('scripts/servicenow/cr_gate.py', 'python'))
out.append("""
## Appendix D: Azure SQL config project examples

Replace these with the team's real tables found in Phase 2; keep the conventions.

`sqlconfig/EtlConfig.sqlproj`""" + code('sqlconfig/EtlConfig.sqlproj', 'xml') +
"`sqlconfig/Tables/etl.source_config.sql`" + code('sqlconfig/Tables/etl.source_config.sql', 'sql') +
"`sqlconfig/Tables/etl.watermark.sql` (runtime state: schema only)" + code('sqlconfig/Tables/etl.watermark.sql', 'sql') +
"`sqlconfig/Data/sources/SAP_SALES.sql` (one MERGE per config key)" + code('sqlconfig/Data/sources/SAP_SALES.sql', 'sql') +
"`sqlconfig/Scripts/Script.PostDeployment.sql`" + code('sqlconfig/Scripts/Script.PostDeployment.sql', 'sql') +
"ADF linked service parameterised by database name (`adf/linkedService/ls_sql_etlconfig.json`)" + code('adf/linkedService/ls_sql_etlconfig.json', 'json'))

out.append(open('handoff/appendix_ef.md').read())
open('HANDOFF.md', 'w').write("\n".join(out) + "\n")
print("written", len("\n".join(out)))
