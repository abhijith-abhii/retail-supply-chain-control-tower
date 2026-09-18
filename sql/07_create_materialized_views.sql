CREATE MATERIALIZED VIEW IF NOT EXISTS mart.mv_monthly_sales AS SELECT * FROM mart.mart_sales_performance WITH NO DATA;
CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_monthly_sales ON mart.mv_monthly_sales(month,category_id,state_id,store_id);
-- First refresh must be non-concurrent; subsequent production refreshes can be concurrent.
REFRESH MATERIALIZED VIEW mart.mv_monthly_sales;
