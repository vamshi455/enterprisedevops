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
### 5.13 Things that are easy to get wrong

- Federated credentials are **not supported on system-assigned managed identities**. If the identities the team wants to reuse
  are system-assigned (e.g. a factory's own identity), new user-assigned identities are needed (max 20 federated credentials each).
- GitHub Environment **required reviewers on private/internal repos need GitHub Enterprise**. Without it, Gates 3, 4 and 6 have no approval step.
- If SQL/Databricks/ADF use private endpoints, GitHub-hosted runners cannot reach them. Use self-hosted runners in the VNet
  (or GitHub-hosted runners with Azure private networking).
- ADF ARM deployments are incremental: deleted objects stay until the post-deployment script removes them.
- Never edit a released `V`-style schema script or a config MERGE to *remove* rows silently. Add a new change that does it explicitly.
- Long-unreleased PRs on main increase drift. Review the `candidates` list (unreleased PRs) at every release planning.

---

## 6. Open questions (answer in Phase 2 from evidence)
""")
out.append("| ID | Question | What it affects | Who can answer |\n|---|---|---|---|")
for q in OPEN:
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
## Appendix C: `scripts/servicenow/cr_gate.py` (reference implementation)
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
