# Databricks notebook source
dbutils.widgets.text("catalog", "dev_shell_data")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------
spark.sql(f"""
CREATE OR REPLACE TABLE {catalog}.silver.sales AS
SELECT DISTINCT order_id, upper(site_code) AS site_code, product_code,
       CAST(volume_l AS DECIMAL(18,3)) AS volume_l, CAST(amount_usd AS DECIMAL(18,2)) AS amount_usd,
       order_ts
FROM {catalog}.bronze.sales_raw
WHERE order_id IS NOT NULL
""")
