-- One file per config key => two PRs rarely touch the same file => clean cherry-picks.
MERGE [etl].[source_config] AS t
USING (VALUES
  ('SAP_SALES', 'SAP', 'abfss://landing@$(LandingAccount).dfs.core.windows.net/sap/sales/',
   'sales_*.csv', '$(UcCatalog).bronze.sales_raw', 'incremental', 'order_ts', 8, 1, 1242)
) AS s (source_code, source_system, landing_path, file_pattern, target_table, load_type, watermark_column, copy_parallelism, is_active, modified_by_pr)
ON t.source_code = s.source_code
WHEN MATCHED THEN UPDATE SET source_system=s.source_system, landing_path=s.landing_path, file_pattern=s.file_pattern,
     target_table=s.target_table, load_type=s.load_type, watermark_column=s.watermark_column,
     copy_parallelism=s.copy_parallelism, is_active=s.is_active, modified_by_pr=s.modified_by_pr
WHEN NOT MATCHED THEN INSERT VALUES (s.source_code, s.source_system, s.landing_path, s.file_pattern, s.target_table,
     s.load_type, s.watermark_column, s.copy_parallelism, s.is_active, s.modified_by_pr);
