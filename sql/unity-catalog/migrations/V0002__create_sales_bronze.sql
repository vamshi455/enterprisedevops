CREATE TABLE IF NOT EXISTS ${catalog}.bronze.sales_raw (
  order_id     STRING,
  site_code    STRING,
  product_code STRING,
  volume_l     DECIMAL(18,3),
  amount_usd   DECIMAL(18,2),
  order_ts     TIMESTAMP,
  _ingest_ts   TIMESTAMP,
  _source_file STRING
) USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
