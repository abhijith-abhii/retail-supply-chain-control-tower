CREATE OR REPLACE VIEW mart.mart_sales_performance AS
 SELECT date_trunc('month',f.date)::date AS month,p.category_id,s.state_id,f.store_id,sum(f.units_sold) units_sold,sum(f.revenue) revenue
 FROM m5.fact_sales_daily f JOIN m5.dim_product p USING(item_id) JOIN m5.dim_store s USING(store_id) GROUP BY 1,2,3,4;
CREATE OR REPLACE VIEW mart.mart_demand_forecast AS SELECT * FROM m5.fact_forecast;
CREATE OR REPLACE VIEW mart.mart_forecast_accuracy AS SELECT model,split_role,store_id,sum(absolute_error)/nullif(sum(actual_units),0) wape,sum(error)/nullif(sum(actual_units),0) bias FROM m5.fact_forecast_accuracy GROUP BY 1,2,3;
CREATE OR REPLACE VIEW mart.mart_inventory_health AS SELECT * FROM m5.fact_inventory_policy;
CREATE OR REPLACE VIEW mart.mart_stockout_risk AS SELECT * FROM m5.fact_inventory_policy WHERE stockout_probability>1-target_service_level;
CREATE OR REPLACE VIEW mart.mart_product_store_performance AS SELECT item_id,store_id,sum(revenue) revenue,sum(units_sold) units_sold,avg(units_sold) mean_units,stddev_samp(units_sold)/nullif(avg(units_sold),0) demand_cv FROM m5.fact_sales_daily GROUP BY 1,2;
CREATE OR REPLACE VIEW mart.mart_delivery_performance AS SELECT * FROM dataco.fact_delivery_performance;
CREATE OR REPLACE VIEW mart.mart_shipping_mode_performance AS SELECT shipping_mode,count(*) FILTER(WHERE delivery_eligible) eligible_orders,sum(late_order) late_orders,avg(late_order::numeric) late_delivery_rate,avg(positive_delay_days) average_delay_days FROM dataco.fact_delivery_performance GROUP BY 1;
CREATE OR REPLACE VIEW mart.mart_profitability AS SELECT o.category,o.market,o.region,sum(p.sales) sales,sum(p.profit) profit,sum(p.profit)/nullif(sum(p.sales),0) profit_margin FROM dataco.fact_orders o JOIN dataco.fact_profitability p USING(order_item_id) WHERE NOT o.invalid_sales_flag GROUP BY 1,2,3;
CREATE OR REPLACE VIEW mart.mart_executive_kpis AS
 SELECT 'M5'::text domain,'historical_revenue'::text metric,sum(revenue) value FROM m5.fact_sales_daily
 UNION ALL SELECT 'M5','forecast_units',sum(forecast_units) FROM m5.fact_forecast
 UNION ALL SELECT 'DataCo','late_delivery_rate',avg(late_order::double precision) FROM dataco.fact_delivery_performance WHERE delivery_eligible
 UNION ALL SELECT 'DataCo','profit',sum(profit) FROM dataco.fact_orders WHERE NOT invalid_sales_flag;
COMMENT ON VIEW mart.mart_executive_kpis IS 'Independent domains stacked as labels; no cross-domain transaction joins or combined profit.';
