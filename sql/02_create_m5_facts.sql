CREATE TABLE IF NOT EXISTS m5.fact_sales_daily (
 item_id text REFERENCES m5.dim_product,store_id text REFERENCES m5.dim_store,date_key integer REFERENCES common.dim_date,
 date date NOT NULL,units_sold double precision NOT NULL CHECK(units_sold>=0),sell_price double precision CHECK(sell_price>=0),revenue double precision,
 wm_yr_wk integer,snap_flag integer CHECK(snap_flag IN (0,1)),event_flag integer CHECK(event_flag IN (0,1)),
 PRIMARY KEY(item_id,store_id,date_key));
CREATE TABLE IF NOT EXISTS m5.fact_sell_price (
 item_id text REFERENCES m5.dim_product,store_id text REFERENCES m5.dim_store,wm_yr_wk integer,sell_price double precision CHECK(sell_price>=0),PRIMARY KEY(item_id,store_id,wm_yr_wk));
COMMENT ON COLUMN m5.fact_sales_daily.revenue IS 'Recorded units times listed weekly price; not accounting net revenue.';
COMMENT ON COLUMN m5.fact_sales_daily.units_sold IS 'Recorded sales, possibly censored by unobserved availability.';
