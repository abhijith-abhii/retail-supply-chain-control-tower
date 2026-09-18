CREATE TABLE IF NOT EXISTS m5.fact_inventory_policy (
 item_id text REFERENCES m5.dim_product,store_id text REFERENCES m5.dim_store,as_of_date date,target_service_level double precision CHECK(target_service_level>0 AND target_service_level<1),
 average_daily_demand double precision,forecast_daily_demand double precision,initial_inventory double precision,
 estimated_unit_cost double precision,safety_stock double precision,reorder_point double precision,eoq double precision,
 days_of_supply double precision,inventory_value double precision,stockout_probability double precision CHECK(stockout_probability BETWEEN 0 AND 1),
 recommended_order_quantity double precision CHECK(recommended_order_quantity>=0),excess_units double precision,excess_value double precision,
 PRIMARY KEY(item_id,store_id,as_of_date,target_service_level));
CREATE TABLE IF NOT EXISTS m5.fact_inventory_simulation (
 item_id text REFERENCES m5.dim_product,store_id text REFERENCES m5.dim_store,date date,policy text,scenario text,run_id integer,target_service_level double precision,
 opening_inventory double precision,arrivals double precision,actual_demand double precision,forecast_demand double precision,
 fulfilled_units double precision,lost_sales_units double precision,order_quantity double precision,in_transit_units double precision,closing_inventory double precision,
 stockout_event integer,holding_cost double precision,ordering_cost double precision,lost_sale_cost double precision,total_inventory_cost double precision,lost_sales_value double precision,
 estimated_unit_cost double precision,completed_cycles integer,successful_cycles integer,
 PRIMARY KEY(item_id,store_id,date,policy,scenario,run_id,target_service_level),
 CHECK(abs(opening_inventory+arrivals-fulfilled_units-closing_inventory)<0.00001),
 CHECK(abs(actual_demand-fulfilled_units-lost_sales_units)<0.00001),CHECK(closing_inventory>=0),CHECK(fulfilled_units>=0));
COMMENT ON TABLE m5.fact_inventory_policy IS 'Scenario recommendations based on simulated inputs. Select one as-of date and service level.';
COMMENT ON TABLE m5.fact_inventory_simulation IS 'Daily lost-sales scenario. Average across Monte Carlo runs; do not sum repeated scenarios.';
