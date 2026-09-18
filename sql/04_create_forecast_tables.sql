CREATE TABLE IF NOT EXISTS m5.fact_forecast (
 item_id text REFERENCES m5.dim_product,store_id text REFERENCES m5.dim_store,date_key integer REFERENCES common.dim_date,
 origin date NOT NULL,date date NOT NULL,horizon integer CHECK(horizon BETWEEN 1 AND 28),model text,
 forecast_units double precision CHECK(forecast_units>=0),lower_80 double precision,upper_80 double precision,lower_95 double precision,upper_95 double precision,
 PRIMARY KEY(item_id,store_id,origin,date_key,model),CHECK(date>origin));
CREATE TABLE IF NOT EXISTS m5.fact_forecast_accuracy (
 item_id text REFERENCES m5.dim_product,store_id text REFERENCES m5.dim_store,date_key integer REFERENCES common.dim_date,
 origin date,date date,model text,fold integer,split_role text,actual_units double precision,forecast_units double precision,error double precision,absolute_error double precision,scale double precision,
 PRIMARY KEY(item_id,store_id,origin,date_key,model));
COMMENT ON COLUMN m5.fact_forecast_accuracy.error IS 'Forecast minus actual; positive means overforecast.';
COMMENT ON COLUMN m5.fact_forecast.lower_95 IS 'Empirical residual interval, approximate coverage, clipped at zero.';
