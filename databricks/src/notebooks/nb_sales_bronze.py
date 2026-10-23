# Databricks notebook source
dbutils.widgets.text("catalog", "dev_shell_data")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------
from pyspark.sql import functions as F

df = (spark.read.option("header", True).csv(f"abfss://landing@{spark.conf.get('shell.landing.account')}.dfs.core.windows.net/sales/")
      .withColumn("_ingest_ts", F.current_timestamp())
      .withColumn("_source_file", F.col("_metadata.file_path")))
df.write.mode("append").saveAsTable(f"{catalog}.bronze.sales_raw")
