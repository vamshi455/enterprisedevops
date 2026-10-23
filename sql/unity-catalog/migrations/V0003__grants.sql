-- Groups are env-scoped in Entra ID / SCIM: e.g. grp-shell-data-qa-readers
GRANT USE CATALOG ON CATALOG ${catalog} TO `grp-shell-data-${env}-readers`;
GRANT USE SCHEMA, SELECT ON SCHEMA ${catalog}.gold TO `grp-shell-data-${env}-readers`;
