from pathlib import Path
from src.utils.file_utils import sql_literal
from src.validation.data_quality import validate_sales

def transform_m5(con, cfg, mode, output):
    con.execute("""CREATE OR REPLACE VIEW unpivoted AS
        UNPIVOT raw_sales ON COLUMNS('^d_[0-9]+$') INTO NAME d VALUE units_sold""")
    con.execute("""CREATE OR REPLACE VIEW joined AS SELECT
        s.id series_id,s.item_id,s.dept_id department_id,s.cat_id category_id,s.store_id,s.state_id,
        s.d,cast(c.date AS DATE) date,cast(strftime(cast(c.date AS DATE),'%Y%m%d') AS INTEGER) date_key,
        s.units_sold,p.sell_price, CASE WHEN s.units_sold=0 THEN 0 ELSE s.units_sold*p.sell_price END revenue,
        c.wm_yr_wk,dayofweek(cast(c.date AS DATE)) weekday,month(cast(c.date AS DATE)) AS month,
        quarter(cast(c.date AS DATE)) AS quarter,year(cast(c.date AS DATE)) AS year,
        c.event_name_1 event_name,c.event_type_1 event_type,c.event_name_2,c.event_type_2,
        CASE s.state_id WHEN 'CA' THEN c.snap_CA WHEN 'TX' THEN c.snap_TX WHEN 'WI' THEN c.snap_WI END snap_flag,
        cast(c.event_name_1 IS NOT NULL OR c.event_name_2 IS NOT NULL AS INTEGER) event_flag,
        cast(dayofweek(cast(c.date AS DATE)) IN (0,6) AS INTEGER) weekend_flag,
        cast(day(cast(c.date AS DATE))=1 AS INTEGER) month_start_flag,
        cast(cast(c.date AS DATE)=last_day(cast(c.date AS DATE)) AS INTEGER) month_end_flag,
        cast(s.units_sold=0 AS INTEGER) zero_sales_flag
        FROM unpivoted s LEFT JOIN calendar c USING(d)
        LEFT JOIN prices p ON s.item_id=p.item_id AND s.store_id=p.store_id AND c.wm_yr_wk=p.wm_yr_wk""")
    # Select the cohort strictly before all validation windows, avoiding selection leakage.
    h=max(cfg['forecast_horizon'],cfg['inventory']['simulation_days'])
    cutoff=con.execute(f"SELECT max(date)-INTERVAL '{h*cfg['backtest_folds']} days' FROM joined").fetchone()[0]
    if mode=='sample':
        con.execute(f"""CREATE OR REPLACE TABLE cohort AS WITH revenue AS (
          SELECT item_id,store_id,sum(revenue) revenue FROM joined
          WHERE date<=? AND date>? - INTERVAL '{cfg['selection_days']} days' GROUP BY ALL),
          stores AS (SELECT store_id FROM revenue GROUP BY store_id ORDER BY sum(revenue) DESC,store_id LIMIT {int(cfg['sample_stores'])})
          SELECT item_id,store_id FROM revenue WHERE store_id IN (SELECT store_id FROM stores)
          ORDER BY revenue DESC,item_id,store_id LIMIT {int(cfg['sample_series'])}""",[cutoff,cutoff])
    else: con.execute("CREATE OR REPLACE TABLE cohort AS SELECT DISTINCT item_id,store_id FROM raw_sales")
    con.execute("CREATE OR REPLACE VIEW sales_long AS SELECT j.* FROM joined j JOIN cohort USING(item_id,store_id)")
    validate_sales(con)
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    con.execute(f"COPY (SELECT * FROM sales_long) TO {sql_literal(output)} (FORMAT PARQUET, PARTITION_BY(store_id,year), OVERWRITE_OR_IGNORE true)")
    con.execute(f"CREATE OR REPLACE VIEW sales AS SELECT * FROM read_parquet({sql_literal(output/'**/*.parquet')},hive_partitioning=true)")
    return cutoff
