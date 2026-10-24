"""Single source of truth for the access-request list (feeds the Excel tracker and the PDF)."""

REPO = "<shell-org>/shell-data-platform"

GRANTORS = {
    "GH": "GitHub org owner",
    "ENTRA": "Entra ID admin / identity owner",
    "AZ": "Azure subscription owner (RBAC)",
    "SQL": "Azure SQL server Entra admin",
    "DBXA": "Databricks account admin",
    "DBXW": "Databricks workspace admin / UC catalog owner",
    "ADO": "Azure DevOps (Boards) project admin",
    "SNOW": "ServiceNow platform admin",
    "NET": "Network / cloud platform team",
    "TEAM": "Existing data/DevOps team (information)",
}

PHASES = {
    "P1": "Start building: DEV, feature-branch testing, PR checks",
    "P2": "First release to QA and UAT",
    "P3": "First release to PROD",
}

# id, area, grantor, principal, envs (D,Q,U,P), permission / action, why, phase, note
R = [
 # ---------------- GitHub
 ("GH-01","GitHub","GH","Vamshi Singam (lead)","",f"Create private/internal repo {REPO}; give the lead Admin role on it during setup","New parallel process needs its own repo with ADF, Databricks and SQL projects side by side","P1",""),
 ("GH-02","GitHub","GH","GitHub teams: developers, tech-leads, release-managers, qa-leads, uat-signoff","","Create or map teams (ideally synced from Entra groups); repo roles: developers = Write, tech-leads = Maintain, release-managers = Maintain","Drives CODEOWNERS review and environment approvers","P1",""),
 ("GH-03","GitHub","GH","Repo settings","","Allow squash merge only (disable merge commits and rebase merge); auto-delete head branches","One PR = one commit on main, which makes releases selectable by PR number","P1",""),
 ("GH-04","GitHub","GH","Ruleset on main","","Require PR; 1 approval from CODEOWNERS (tech-leads); dismiss stale approvals; require status check 'pr-validation'; require conversation resolution; block force-push and deletion; no bypass except org admins","Gate 1: only reviewed, tested PRs reach main","P1",""),
 ("GH-05","GitHub","GH","Ruleset on release/* branches and prod/* tags","","Restrict create/update/delete; bypass list = release-bot GitHub App only","Nobody hand-edits a release branch or moves a production tag","P2",""),
 ("GH-06","GitHub","GH","GitHub App 'shell-data-release-bot'","","Create app (Contents: read & write, Pull requests: read, Metadata: read), install on the repo only; give its App ID and private key to the lead for the 'release-cut' environment secret","Cuts release/<id> branches and pushes prod/<id> tags past the ruleset in GH-05","P2",""),
 ("GH-07","GitHub","GH","GitHub Actions policy","","Enable Actions on the repo; allow actions: actions/*, azure/login, databricks/setup-cli, Azure/arm-deploy, Azure/sql-action (or allow 'verified creators')","Workflows for validation, feature environments and releases","P1",""),
 ("GH-08","GitHub","GH","Workflow permissions / OIDC","","Default GITHUB_TOKEN = read; workflows may request id-token: write (OIDC). Confirm no org policy blocks OIDC","Passwordless sign-in to Azure with the existing managed identities","P1",""),
 ("GH-09","GitHub","GH","GitHub Environments","D,Q,U,P","Create environments: dev-feature, dev, release-cut, qa, uat, prod. Required reviewers: qa = qa-leads, uat = uat-signoff, prod = release-managers. Deployment branches: dev-feature = feature/**, bugfix/**; dev = main; release-cut = main; qa/uat/prod = release/*","Gates 3, 4 and 6 are environment approvals","P1","Required reviewers on a private/internal repo need GitHub Enterprise (confirm plan, see OQ-07)"),
 ("GH-10","GitHub","GH","Environment secrets","U,P","Store ServiceNow integration credentials as secrets in the 'prod' environment only (and 'uat' if the CR is checked before UAT)","Gate 5 reads and updates the change request","P3",""),
 ("GH-11","GitHub","GH","Third-party app access","D","Approve the 'Azure Data Factory' and 'Databricks' GitHub apps / OAuth apps for the org (if OAuth app access restrictions are on)","DEV factory Git mode and Databricks Git folders must read feature branches: this is what makes feature-branch testing possible","P1","Blocking for feature testing"),
 ("GH-12","GitHub","GH","GitHub Actions runners","D,Q,U,P","GitHub-hosted runners if Azure endpoints are public. If ADF/SQL/Databricks are private: self-hosted runners in a VNet with line of sight (or GitHub-hosted runners with Azure private networking), registered to this repo","Runners must reach SQL (DACPAC), Databricks and ARM endpoints","P1","Depends on OQ-03"),
 # ---------------- Entra / identities
 ("ID-01","Identity","ENTRA","Existing managed identities","D,Q,U,P","Confirm each identity we reuse is USER-assigned and give: name, client ID, object ID, resource group, tenant ID","GitHub can only sign in through a user-assigned identity (or app registration); system-assigned identities (for example the factory's own) cannot take federated credentials","P1","If they are system-assigned, request one user-assigned identity per environment instead (see OQ-04)"),
 ("ID-02","Identity","ENTRA","Deploy identity – DEV","D","Add federated credentials: issuer https://token.actions.githubusercontent.com, audience api://AzureADTokenExchange, subjects repo:<shell-org>/shell-data-platform:environment:dev and …:environment:dev-feature","deploy-dev and feature-env workflows","P1","Needs Contributor/Owner on the identity to add"),
 ("ID-03","Identity","ENTRA","CI identity (read-only) – DEV","D","Federated credential subject repo:<shell-org>/shell-data-platform:pull_request (a separate low-privilege identity is preferred; DEV deploy identity acceptable)","pr-validation runs ADF validate and bundle validate against DEV","P1",""),
 ("ID-04","Identity","ENTRA","Deploy identity – QA, UAT","Q,U","Federated credentials with subjects …:environment:qa and …:environment:uat (on each environment's identity)","release workflow QA and UAT jobs","P2",""),
 ("ID-05","Identity","ENTRA","Deploy identity – PROD","P","Federated credential with subject …:environment:prod","release workflow PROD job (runs only after release-manager approval)","P3",""),
 ("ID-06","Identity","ENTRA","Entra security groups","","Create or confirm groups: grp-data-developers, grp-data-techleads, grp-data-qa, grp-data-uat-signoff, grp-data-release-managers","Used for Azure RBAC, SQL, Databricks and GitHub team sync","P1",""),
 # ---------------- Azure RBAC
 ("AZ-01","Azure RBAC","AZ","Deploy identity – each env","D,Q,U,P","Data Factory Contributor on the resource group that holds that environment's factory","ARM template deployment, stop/start triggers, delete removed pipelines","P1 DEV · P2 QA/UAT · P3 PROD",""),
 ("AZ-02","Azure RBAC","AZ","Deploy identity – DEV","D","SQL DB Contributor on the DEV SQL logical server","Create, copy and drop feature databases sqldb-etlcfg-ft-<story>","P1","DEV only"),
 ("AZ-03","Azure RBAC","AZ","DEV SQL logical server","D","Create elastic pool 'pool-etlcfg-feature' (small, e.g. GP 2 vCore or 50–100 eDTU) on the DEV server; name a cost owner","Feature databases share one capped pool; nightly cleanup keeps it small","P1","Sizing/cost decision (OQ-05)"),
 ("AZ-04","Azure RBAC","AZ","Deploy identity – each env","D,Q,U,P","Reader on the environment's data-platform resource group(s)","Look up resource IDs, run ARM what-if","P1 DEV · P2 QA/UAT · P3 PROD",""),
 ("AZ-05","Azure RBAC","AZ","grp-data-developers","D","Data Factory Contributor on the DEV factory only","Author in Git mode and debug pipelines on feature branches","P1","No write access to QA/UAT/PROD factories"),
 ("AZ-06","Azure RBAC","AZ","grp-data-developers","Q,U,P","Reader (or Data Factory monitoring via Reader) on QA/UAT/PROD factories","Monitor runs without changing anything","P2",""),
 ("AZ-07","Azure RBAC","AZ","Factory managed identity (existing) – each env","D,Q,U,P","Verify existing: Storage Blob Data Contributor on ADLS; Key Vault Secrets User on the Key Vault used by linked services","Pipelines keep working after deployments","P1","Verification only"),
 # ---------------- Azure SQL
 ("SQL-01","Azure SQL","SQL","Each config SQL logical server","D,Q,U,P","Confirm Microsoft Entra admin is set and Entra authentication is enabled; give server and database names","Identities sign in without passwords","P1",""),
 ("SQL-02","Azure SQL","SQL","Deploy identity – each env","D,Q,U,P","In the config DB: CREATE USER [<deploy-identity>] FROM EXTERNAL PROVIDER; ALTER ROLE db_owner ADD MEMBER [<deploy-identity>]","DACPAC deploys schema, permissions and config rows","P1 DEV · P2 QA/UAT · P3 PROD","In DEV this user is copied into every feature DB automatically"),
 ("SQL-03","Azure SQL","SQL","Factory managed identity (existing) – each env","D,Q,U,P","Verify it is a user in the config DB with db_datareader, db_datawriter and EXECUTE","ADF reads config and writes watermarks; copied into feature DBs automatically","P1","Verification only"),
 ("SQL-04","Azure SQL","SQL","grp-data-developers","D","db_datareader on sqldb-etlcfg-dev","Inspect config; the feature-env workflow grants write access on each feature DB itself","P1",""),
 ("SQL-05","Azure SQL","NET","Config SQL servers – network","D,Q,U,P","Allow the runners from GH-12 to reach port 1433: private endpoint + VNet runners, or firewall rule for static runner IPs","DACPAC deployment and feature-DB setup","P1","Depends on OQ-03"),
 # ---------------- Databricks
 ("DBX-01","Databricks","DBXA","Deploy identity – each env","D,Q,U,P","Add the identity (by client ID) as a service principal in the Databricks account; assign it to that environment's workspace with 'Workspace access'","Databricks CLI deploys asset bundles as this identity","P1 DEV · P2 QA/UAT · P3 PROD",""),
 ("DBX-02","Databricks","DBXW","Deploy identity – each env","D,Q,U,P","CAN MANAGE on the bundle root folder (e.g. /Workspace/Shared/shell-data); allowed to create jobs","bundle deploy creates and updates jobs, notebooks and pipelines","P1 DEV · P2 QA/UAT · P3 PROD",""),
 ("DBX-03","Databricks","DBXW","Deploy identity – each env","D,Q,U,P","CAN USE on the job cluster policy, or serverless jobs enabled","Jobs defined in the bundle can start compute","P1 DEV · P2 QA/UAT · P3 PROD","Depends on OQ-02"),
 ("DBX-04","Databricks","DBXW","Deploy identity – each env","D,Q,U,P","If jobs run as an existing run-as service principal: 'Service Principal: User' role on that principal","Bundle sets run_as on production jobs","P2",""),
 ("DBX-05","Databricks","DBXW","Deploy identity – each env","D,Q,U,P","Unity Catalog on the environment catalog: USE CATALOG, USE SCHEMA, CREATE SCHEMA, CREATE TABLE, CREATE FUNCTION, CREATE VOLUME, MODIFY, SELECT (or ownership of bundle-managed schemas)","Bundle-managed DDL and grants","P1 DEV · P2 QA/UAT · P3 PROD",""),
 ("DBX-06","Databricks","DBXW","Deploy identity – each env","D,Q,U,P","CAN USE on one SQL warehouse","Run UC SQL steps during deployment","P1 DEV · P2 QA/UAT · P3 PROD",""),
 ("DBX-07","Databricks","DBXW","Factory managed identity (existing) – each env","D,Q,U,P","Verify it is a workspace service principal; give its client ID so the bundle grants it CAN MANAGE RUN on the jobs it triggers","ADF triggers Databricks jobs after every deployment","P1","Verification + information"),
 ("DBX-08","Databricks","DBXW","grp-data-developers","D","DEV workspace access; serverless/cluster use; on dev catalog: USE CATALOG, CREATE SCHEMA (personal dev_<user> schemas)","Developers deploy bundles in development mode: resources prefixed with their name, isolated per developer","P1",""),
 ("DBX-09","Databricks","DBXW","DEV workspace – Git integration","D","Allow Git folders to the GitHub org (add repo to the Git allowlist if restricted)","Developers work on feature branches inside the workspace","P1",""),
 # ---------------- ADF config
 ("ADF-01","ADF","AZ","DEV factory","D","Connect the DEV factory to GitHub: repo shell-data-platform, collaboration branch main, root folder /adf; turn ON 'Disable publish' (automated publish)","Feature branches can be debugged; main is deployed by the pipeline, not the Publish button","P1","Done by the lead once AZ-05 and GH-11 are granted"),
 ("ADF-02","ADF","TEAM","Integration runtimes","D,Q,U,P","Names/types of integration runtimes (Azure, self-hosted, shared/linked) used by each factory","ARM parameter files map linked services to the right runtime per environment","P1","Information"),
 # ---------------- Azure Boards
 ("ADO-01","Azure Boards","ADO","Azure Boards app","","Install the Azure Boards app on the GitHub org and connect the ADO project to shell-data-platform (needs ADO project admin + GitHub org owner)","AB#1234 in a PR links it to the story; PR check blocks merges without a story","P1",""),
 ("ADO-02","Azure Boards","ADO","Deploy identity (QA/UAT/PROD, or one release identity)","Q,U,P","Add the managed identity to the Azure DevOps organization (Basic access); Contributor on the project or area path","Release workflow moves stories to Ready for QA / Ready for UAT / Closed and comments the release id","P2",""),
 ("ADO-03","Azure Boards","TEAM","Board process","","Confirm work-item state names and the area path used by this team","Workflow uses the exact state names","P2","Information"),
 # ---------------- ServiceNow
 ("SN-01","ServiceNow","SNOW","Integration account / OAuth client","P","Integration user (or OAuth client credentials) able to read change_request and update state and work_notes for this team's assignment group","Gate 5: CR approved + in window + PR list matches; evidence written back after deploy","P3",""),
 ("SN-02","ServiceNow","SNOW","Change template","P","Add a field (e.g. u_release_prs) or agree the description lines 'Release-Id:' and 'Release-PRs:' on the CR template; confirm change model (Normal/Standard)","Ties each CR to the exact PRs being deployed","P3",""),
 ("SN-03","ServiceNow","NET","ServiceNow instance – network","P","If the instance restricts inbound IPs, allow the runner egress IPs","Runners call the ServiceNow Table API","P3","Conditional"),
]

OPEN = [
 ("OQ-01","Is each environment (DEV, QA, UAT, PROD) in its own subscription? Resource group and resource names per env?","Scopes for every Azure role assignment","Vamshi / platform team"),
 ("OQ-02","Is Databricks serverless (jobs and SQL) allowed, or must jobs use a cluster policy?","DBX-03 and bundle job definitions","Databricks admin"),
 ("OQ-03","Are ADF, Azure SQL and Databricks behind private endpoints? Which self-hosted integration runtimes exist?","Runner choice (GH-12), SQL-05, ADF-02","Network team"),
 ("OQ-04","Are the managed identities we must reuse user-assigned or system-assigned?","If system-assigned, GitHub cannot use them: new user-assigned identities are needed","Entra admin"),
 ("OQ-05","Elastic pool size and cost owner for feature databases","AZ-03","Budget owner"),
 ("OQ-06","How are Azure SQL scripts deployed today (SQL project/DACPAC, numbered scripts, other)?","Decides the SQL project tooling; process stays the same","Existing team"),
 ("OQ-07","Which GitHub plan does the org have (Enterprise Cloud?)","Environment required reviewers on private/internal repos need GitHub Enterprise","GitHub org owner"),
 ("OQ-08","ServiceNow: assignment group, change model, and whether CRs can be read/updated via API","SN-01, SN-02","ServiceNow admin"),
]

FILLIN = [  # names the admins return
 ("Tenant ID","","","",""),
 ("Subscription ID","","","",""),
 ("Resource group (data platform)","","","",""),
 ("Deploy identity name (user-assigned)","","","",""),
 ("Deploy identity client ID","","","",""),
 ("Data Factory name","adf-…-dev","","",""),
 ("Factory managed identity client ID","","","",""),
 ("SQL logical server","","","",""),
 ("Config database","sqldb-etlcfg-dev","","",""),
 ("Databricks workspace URL","https://adb-….azuredatabricks.net","","",""),
 ("Unity Catalog catalog","","","",""),
 ("SQL warehouse ID","","","",""),
 ("Self-hosted IR name (if any)","","","",""),
 ("Key Vault name","","","",""),
]
