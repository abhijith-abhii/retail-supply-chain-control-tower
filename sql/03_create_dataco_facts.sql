CREATE TABLE IF NOT EXISTS dataco.fact_delivery_performance (
 order_id bigint PRIMARY KEY, date_key integer REFERENCES dataco.dim_order_date,order_date date,
 shipping_mode text REFERENCES dataco.dim_shipping_mode,market text REFERENCES dataco.dim_market,
 region text REFERENCES dataco.dim_region,customer_segment text REFERENCES dataco.dim_customer_segment,
 actual_shipping_days double precision,scheduled_shipping_days double precision,
 delivery_eligible boolean NOT NULL,late_order integer CHECK(late_order IN(0,1)),delay_days double precision,positive_delay_days double precision);
CREATE TABLE IF NOT EXISTS dataco.fact_orders (
 order_item_id bigint PRIMARY KEY,order_id bigint NOT NULL REFERENCES dataco.fact_delivery_performance,
 date_key integer REFERENCES dataco.dim_order_date,order_date date,
 category text REFERENCES dataco.dim_product_category,market text REFERENCES dataco.dim_market,
 region text REFERENCES dataco.dim_region,shipping_mode text REFERENCES dataco.dim_shipping_mode,
 customer_segment text REFERENCES dataco.dim_customer_segment,product_name text,quantity double precision,
 sales double precision,profit double precision,invalid_sales_flag boolean,abnormal_profit_flag boolean);
CREATE TABLE IF NOT EXISTS dataco.fact_profitability (
 order_item_id bigint PRIMARY KEY REFERENCES dataco.fact_orders,sales double precision,profit double precision,profit_margin double precision,loss_making_line boolean);
COMMENT ON TABLE dataco.fact_orders IS 'One row per order item, not one per order. Order IDs legitimately repeat.';
COMMENT ON TABLE dataco.fact_profitability IS 'Line-level configured source sales and benefit. Never sum repeated order total columns.';
COMMENT ON COLUMN dataco.fact_delivery_performance.late_order IS 'Derived actual duration > promise. Null for ineligible or absent durations.';
