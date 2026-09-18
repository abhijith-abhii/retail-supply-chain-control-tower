"""Transactional reload of this project's schemas only. Stream Parquet batches into PostgreSQL."""
import os
from pathlib import Path
import pyarrow.parquet as pq
from sqlalchemy import create_engine,inspect,text
from dotenv import load_dotenv

MAPPING=[('dim_date','common','dim_date'),('dim_state','m5','dim_state'),('dim_category','m5','dim_category'),
 ('dim_department','m5','dim_department'),('dim_store','m5','dim_store'),('dim_product','m5','dim_product'),('dim_event','m5','dim_event'),('bridge_date_event','m5','bridge_date_event'),
 ('dim_order_date','dataco','dim_order_date'),('dim_product_category','dataco','dim_product_category'),('dim_market','dataco','dim_market'),('dim_region','dataco','dim_region'),('dim_shipping_mode','dataco','dim_shipping_mode'),('dim_customer_segment','dataco','dim_customer_segment'),
 ('sales_daily','m5','fact_sales_daily'),('fact_sell_price','m5','fact_sell_price'),('dataco_delivery_performance','dataco','fact_delivery_performance'),
 ('dataco_profitability','dataco','fact_orders'),('dataco_profitability','dataco','fact_profitability'),
 ('demand_forecasts_28d','m5','fact_forecast'),('forecast_backtest_all','m5','fact_forecast_accuracy'),
 ('inventory_policy_recommendations','m5','fact_inventory_policy'),('inventory_simulation_daily','m5','fact_inventory_simulation')]

def load_database(out,sql_dir):
    load_dotenv();url=os.environ.get('DATABASE_URL')
    if not url: raise ValueError('DATABASE_URL must be configured; use .env.example')
    engine=create_engine(url)
    with engine.begin() as conn:
        for p in sorted(Path(sql_dir).glob('0[0-5]_*.sql')): conn.exec_driver_sql(p.read_text())
        # Dedicated database recommended. One atomic snapshot avoids stale mixed-run rows.
        targets=','.join(f'{s}.{t}' for _,s,t in MAPPING)
        conn.exec_driver_sql('TRUNCATE '+targets)
        inspector=inspect(conn)
        for source,schema,table in MAPPING:
            fields={c['name'] for c in inspector.get_columns(table,schema=schema)}
            parquet=pq.ParquetFile(Path(out)/(source+'.parquet'))
            selected=[n for n in parquet.schema_arrow.names if n in fields]
            for batch in parquet.iter_batches(batch_size=10000,columns=selected):
                frame=batch.to_pandas()
                frame.to_sql(table,conn,schema=schema,if_exists='append',index=False,chunksize=1000,method=None)
        for p in sorted(Path(sql_dir).glob('0[6-8]_*.sql')): conn.exec_driver_sql(p.read_text())
        comments=Path(sql_dir)/'10_document_columns.sql'
        if comments.exists(): conn.exec_driver_sql(comments.read_text())
        failures=conn.exec_driver_sql((Path(sql_dir)/'09_data_quality_tests.sql').read_text()).fetchall()
        if any(n for _,n in failures): raise ValueError(f'SQL quality checks failed: {failures}')
    engine.dispose()
