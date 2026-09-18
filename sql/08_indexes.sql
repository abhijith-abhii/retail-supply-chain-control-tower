CREATE INDEX IF NOT EXISTS ix_sales_date_store ON m5.fact_sales_daily(date_key,store_id) INCLUDE(revenue,units_sold);
CREATE INDEX IF NOT EXISTS ix_sales_date_brin ON m5.fact_sales_daily USING brin(date);
CREATE INDEX IF NOT EXISTS ix_orders_order ON dataco.fact_orders(order_id);
CREATE INDEX IF NOT EXISTS ix_orders_category_date ON dataco.fact_orders(category,date_key);
CREATE INDEX IF NOT EXISTS ix_delivery_late ON dataco.fact_delivery_performance(shipping_mode,order_date) WHERE late_order=1;
CREATE INDEX IF NOT EXISTS ix_forecast_origin ON m5.fact_forecast(origin,date_key);
ANALYZE m5.fact_sales_daily;
ANALYZE dataco.fact_orders;
