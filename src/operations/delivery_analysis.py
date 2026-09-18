import pandas as pd

def delivery_summary(delivery):
    rows=[]
    for dim in ['shipping_mode','market','region','customer_segment']:
        for val,g in delivery.groupby(dim):
            eligible=g[g.delivery_eligible]
            rows.append(dict(dimension=dim,segment=val,total_orders=len(g),eligible_orders=len(eligible),
              late_orders=int(eligible.late_order.sum()),late_delivery_rate=eligible.late_order.mean() if len(eligible) else None,
              average_delay_days=eligible.positive_delay_days.mean(),average_signed_delay=eligible.delay_days.mean(),
              actual_shipping_days=eligible.actual_shipping_days.mean(),scheduled_shipping_days=eligible.scheduled_shipping_days.mean()))
    return pd.DataFrame(rows)

def category_delivery(lines,delivery):
    # DISTINCT order-category, so a multi-category order appears once in each applicable category.
    x=lines[['order_id','category']].drop_duplicates().merge(delivery,on='order_id',validate='many_to_one')
    return x.groupby('category').agg(orders=('order_id','nunique'),eligible_orders=('delivery_eligible','sum'),late_orders=('late_order','sum')).assign(late_delivery_rate=lambda x:x.late_orders/x.eligible_orders.replace(0,float('nan'))).reset_index()
