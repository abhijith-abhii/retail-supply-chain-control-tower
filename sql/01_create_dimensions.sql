CREATE TABLE IF NOT EXISTS common.dim_date (
 date_key integer PRIMARY KEY, date date NOT NULL UNIQUE, year integer NOT NULL, month integer CHECK(month BETWEEN 1 AND 12), quarter integer CHECK(quarter BETWEEN 1 AND 4));
CREATE TABLE IF NOT EXISTS m5.dim_state (state_id text PRIMARY KEY);
CREATE TABLE IF NOT EXISTS m5.dim_category (category_id text PRIMARY KEY);
CREATE TABLE IF NOT EXISTS m5.dim_department (department_id text PRIMARY KEY, category_id text NOT NULL REFERENCES m5.dim_category);
CREATE TABLE IF NOT EXISTS m5.dim_store (store_id text PRIMARY KEY,state_id text NOT NULL REFERENCES m5.dim_state);
CREATE TABLE IF NOT EXISTS m5.dim_product (item_id text PRIMARY KEY,department_id text NOT NULL REFERENCES m5.dim_department,category_id text NOT NULL REFERENCES m5.dim_category);
CREATE TABLE IF NOT EXISTS m5.dim_event (event_name text PRIMARY KEY,event_type text);
CREATE TABLE IF NOT EXISTS m5.bridge_date_event (date_key integer REFERENCES common.dim_date,event_name text REFERENCES m5.dim_event,PRIMARY KEY(date_key,event_name));
CREATE TABLE IF NOT EXISTS dataco.dim_order_date (date_key integer PRIMARY KEY REFERENCES common.dim_date,date date UNIQUE NOT NULL,year integer,month integer,quarter integer);
CREATE TABLE IF NOT EXISTS dataco.dim_product_category (category text PRIMARY KEY);
CREATE TABLE IF NOT EXISTS dataco.dim_market (market text PRIMARY KEY);
CREATE TABLE IF NOT EXISTS dataco.dim_region (region text PRIMARY KEY);
CREATE TABLE IF NOT EXISTS dataco.dim_shipping_mode (shipping_mode text PRIMARY KEY);
CREATE TABLE IF NOT EXISTS dataco.dim_customer_segment (customer_segment text PRIMARY KEY);
COMMENT ON TABLE m5.bridge_date_event IS 'Supports both M5 calendar events on the same date; avoid fan-out of sales.';
