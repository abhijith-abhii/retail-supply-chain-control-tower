-- Every returned failure count must equal zero. Foreign keys additionally enforce integrity at load time.
SELECT 'negative_sales_units' test,count(*) failures FROM m5.fact_sales_daily WHERE units_sold<0
UNION ALL SELECT 'negative_prices',count(*) FROM m5.fact_sell_price WHERE sell_price<0
UNION ALL SELECT 'sales_orphan_product',count(*) FROM m5.fact_sales_daily s LEFT JOIN m5.dim_product p USING(item_id) WHERE p.item_id IS NULL
UNION ALL SELECT 'sales_orphan_date',count(*) FROM m5.fact_sales_daily s LEFT JOIN common.dim_date d USING(date_key) WHERE d.date_key IS NULL
UNION ALL SELECT 'sales_date_key_mismatch',count(*) FROM m5.fact_sales_daily s JOIN common.dim_date d USING(date_key) WHERE s.date<>d.date
UNION ALL SELECT 'forecast_alignment',count(*) FROM m5.fact_forecast WHERE date-origin<>horizon OR forecast_units<0
UNION ALL SELECT 'invalid_intervals',count(*) FROM m5.fact_forecast WHERE lower_95>lower_80 OR lower_80>forecast_units OR upper_80<forecast_units OR upper_95<upper_80
UNION ALL SELECT 'invalid_service',count(*) FROM m5.fact_inventory_policy WHERE target_service_level<=0 OR target_service_level>=1
UNION ALL SELECT 'inventory_balance',count(*) FROM m5.fact_inventory_simulation WHERE abs(opening_inventory+arrivals-fulfilled_units-closing_inventory)>0.00001
UNION ALL SELECT 'invalid_fulfillment',count(*) FROM m5.fact_inventory_simulation WHERE fulfilled_units>actual_demand OR fulfilled_units<0
UNION ALL SELECT 'invalid_late_rate',count(*) FROM mart.mart_shipping_mode_performance WHERE late_delivery_rate NOT BETWEEN 0 AND 1
UNION ALL SELECT 'pii_columns',count(*) FROM information_schema.columns WHERE table_schema IN ('m5','dataco','mart') AND column_name ~ '(email|password|phone|street|customer_fname|customer_lname|customer_id)';
