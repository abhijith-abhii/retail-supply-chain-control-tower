import pandas as pd
from src.utils.file_utils import export_frame

def build_dimensions(con,lines,delivery,out):
    queries={
    'dim_date':"SELECT DISTINCT cast(date AS DATE) date,cast(strftime(cast(date AS DATE),'%Y%m%d') AS INTEGER) date_key,year(cast(date AS DATE)) AS year,month(cast(date AS DATE)) AS month,quarter(cast(date AS DATE)) AS quarter FROM calendar",
    'dim_product':"SELECT DISTINCT item_id,department_id,category_id FROM sales",
    'dim_store':"SELECT DISTINCT store_id,state_id FROM sales",
    'dim_state':"SELECT DISTINCT state_id FROM sales",
    'dim_category':"SELECT DISTINCT category_id FROM sales",
    'dim_department':"SELECT DISTINCT department_id,category_id FROM sales",
    'dim_event':"SELECT DISTINCT event_name,event_type FROM (SELECT event_name_1 event_name,event_type_1 event_type FROM calendar UNION SELECT event_name_2,event_type_2 FROM calendar) WHERE event_name IS NOT NULL",
    'bridge_date_event':"SELECT DISTINCT cast(strftime(cast(date AS DATE),'%Y%m%d') AS INTEGER) date_key,event_name FROM (SELECT date,event_name_1 event_name FROM calendar UNION SELECT date,event_name_2 FROM calendar) WHERE event_name IS NOT NULL",
    'fact_sell_price':"SELECT DISTINCT item_id,store_id,wm_yr_wk,sell_price FROM sales WHERE sell_price IS NOT NULL"}
    dims={name:con.execute(q).df() for name,q in queries.items()}
    dates=pd.date_range(min(pd.to_datetime(dims['dim_date'].date).min(),lines.order_date.min()),max(pd.to_datetime(dims['dim_date'].date).max(),lines.order_date.max()))
    dims['dim_date']=pd.DataFrame({'date':dates,'date_key':dates.strftime('%Y%m%d').astype(int),'year':dates.year,'month':dates.month,'quarter':dates.quarter})
    dims['dim_order_date']=dims['dim_date'].copy()
    for name,col in [('dim_product_category','category'),('dim_market','market'),('dim_region','region'),('dim_shipping_mode','shipping_mode'),('dim_customer_segment','customer_segment')]: dims[name]=lines[[col]].drop_duplicates()
    for name,df in dims.items():
        if df.iloc[:,0].duplicated().any() and not name.startswith(('bridge','fact')): raise ValueError('Dimension key not unique: '+name)
        export_frame(df,name,out)
    return dims
