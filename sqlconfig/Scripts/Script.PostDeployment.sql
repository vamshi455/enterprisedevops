/* Post-deployment: idempotent config DATA. Runs on every deploy, in every environment.
   Environment-specific values come from SQLCMD variables ($(Env), $(LandingAccount), $(UcCatalog)).
   Add one :r line per new Data file. Never include runtime tables (etl.watermark, etl.run_log). */
PRINT 'Applying ETL config for $(Env)';
:r ..\Data\sources\SAP_SALES.sql
