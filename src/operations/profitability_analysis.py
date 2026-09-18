import numpy as np
import pandas as pd

def profitability(lines):
    good=lines[~lines.invalid_sales_flag]
    result=[]
    for dim in ['category','market','region','product_name','customer_segment']:
        g=good.groupby(dim).agg(sales=('sales',lambda x:x.sum(min_count=1)),profit=('profit',lambda x:x.sum(min_count=1)),order_count=('order_id','nunique')).reset_index().rename(columns={dim:'segment'})
        g['dimension']=dim;g['profit_margin']=g.profit.div(g.sales.replace(0,np.nan));result.append(g)
    order=good.groupby('order_id').agg(sales=('sales',lambda x:x.sum(min_count=1)),profit=('profit',lambda x:x.sum(min_count=1))).reset_index()
    order['loss_making_order']=order.profit<0
    return pd.concat(result,ignore_index=True),order
