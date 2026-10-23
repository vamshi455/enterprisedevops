-- Medallion schemas. ${catalog} resolves to dev_shell_data / qa_shell_data / uat_shell_data / prod_shell_data
CREATE SCHEMA IF NOT EXISTS ${catalog}.bronze COMMENT 'Raw ingested data (ADF landing -> Delta)';
CREATE SCHEMA IF NOT EXISTS ${catalog}.silver COMMENT 'Cleansed, conformed data';
CREATE SCHEMA IF NOT EXISTS ${catalog}.gold   COMMENT 'Business-ready marts';
