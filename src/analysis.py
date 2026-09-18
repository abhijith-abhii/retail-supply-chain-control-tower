import numpy as np
import pandas as pd
from src.utils.file_utils import export_frame

def history_summary(con,origin):
    return con.execute("""SELECT item_id,store_id,category_id,department_id,state_id,
       avg(units_sold) average_daily_demand,stddev_samp(units_sold) demand_std,
       sum(revenue) revenue,sum(units_sold) units_sold,
       avg(zero_sales_flag) zero_demand_share,arg_max(sell_price,date) last_price
       FROM sales WHERE date<=? AND date>? - INTERVAL '90 days' GROUP BY ALL""",[origin,origin]).df()

def segmentation(history,cfg):
    x=history.sort_values(['revenue','item_id','store_id'],ascending=[False,True,True]).copy()
    total=x.revenue.sum();prior=(x.revenue.cumsum()-x.revenue)/(total or 1)
    x['abc']=np.select([prior<.8,prior<.95],['A','B'],default='C') if total>0 else 'C'
    x['coefficient_of_variation']=x.demand_std/x.average_daily_demand.replace(0,np.nan)
    a,b=cfg['xyz_cv_thresholds'];x['xyz']=np.select([(x.coefficient_of_variation<=a)&(x.zero_demand_share<cfg['intermittent_zero_share']),
        (x.coefficient_of_variation<=b)&(x.zero_demand_share<cfg['intermittent_zero_share'])],['X','Y'],default='Z')
    x['abc_xyz']=x.abc+'-'+x.xyz
    q=x.average_daily_demand.rank(pct=True,method='average');x['volume_segment']=np.select([q<=1/3,q<=2/3],['low','medium'],default='high')
    x['cumulative_revenue_share']=x.revenue.cumsum()/(total or 1)
    return x

def eda(con,lines,delivery,cfg,out):
    tables={}
    for name,grain in [('sales_monthly',"date_trunc('month',date)"),('sales_weekly',"date_trunc('week',date)"),('sales_trend','date')]:
        tables[name]=con.execute(f'SELECT {grain} period,sum(units_sold) units_sold,sum(revenue) revenue FROM sales GROUP BY 1 ORDER BY 1').df()
    for col in ['category_id','department_id','item_id','store_id','state_id','weekday','month','event_name','snap_flag']:
        tables['m5_by_'+col]=con.execute(f'SELECT {col},sum(units_sold) units_sold,sum(revenue) revenue,avg(units_sold) mean_series_day_units,count(*) series_days FROM sales GROUP BY 1').df()
    tables['price_demand_association']=con.execute('SELECT item_id,store_id,corr(price_change_percentage,units_sold) price_change_demand_correlation FROM features GROUP BY ALL').df()
    end=con.execute('SELECT max(date) FROM sales').fetchone()[0]
    tables['product_store_performance']=segmentation(history_summary(con,end),cfg)
    tables['abc_xyz_segmentation']=tables['product_store_performance'][['item_id','store_id','abc','xyz','abc_xyz','volume_segment','coefficient_of_variation','cumulative_revenue_share']]
    monthly=lines.assign(period=lines.order_date.dt.to_period('M').dt.to_timestamp()).groupby('period').agg(sales=('sales','sum'),profit=('profit','sum'),orders=('order_id','nunique')).reset_index()
    tables['dataco_monthly']=monthly
    for name,x in tables.items(): export_frame(x,name,out)
    return tables
