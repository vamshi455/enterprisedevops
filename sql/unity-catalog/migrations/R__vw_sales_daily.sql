-- Repeatable: re-applied whenever this file's checksum changes
CREATE OR REPLACE VIEW ${catalog}.gold.vw_sales_daily AS
SELECT site_code, product_code, CAST(order_ts AS DATE) AS order_date,
       SUM(volume_l) AS volume_l, SUM(amount_usd) AS amount_usd
FROM ${catalog}.silver.sales
GROUP BY ALL;
