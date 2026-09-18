import numpy as np
import pandas as pd
LAGS=[1,7,14,28,56]
CATEGORICAL=['item_id','store_id','state_id','category_id','department_id','event_type']
NUMERIC=[f'lag_{x}' for x in LAGS]+[f'rolling_mean_{x}' for x in [7,28,56]]+['rolling_std_7','rolling_std_28','sell_price','price_change_percentage','weekday','week','month','quarter','event_flag','snap_flag','days_since_last_sale']
FEATURES=NUMERIC+CATEGORICAL

def create_feature_view(con):
    windows=[]
    for lag in LAGS: windows.append(f'lag(units_sold,{lag}) OVER w AS lag_{lag}')
    for days in [7,28,56]:
        frame=f'PARTITION BY item_id,store_id ORDER BY date ROWS BETWEEN {days} PRECEDING AND 1 PRECEDING'
        windows.append(f'avg(units_sold) OVER ({frame}) rolling_mean_{days}')
        if days in [7,28]:
            windows += [f'stddev_samp(units_sold) OVER ({frame}) rolling_std_{days}',f'sum(units_sold) OVER ({frame}) rolling_{days}_day_units',f'sum(revenue) OVER ({frame}) rolling_{days}_day_revenue']
    con.execute("CREATE OR REPLACE VIEW features AS SELECT *,weekofyear(date) AS week,"+','.join(windows)+""",
      sell_price/nullif(lag(sell_price) OVER w,0)-1 price_change_percentage,
      date_diff('day',max(CASE WHEN units_sold>0 THEN date END) OVER
        (PARTITION BY item_id,store_id ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),date) days_since_last_sale
      FROM sales WINDOW w AS (PARTITION BY item_id,store_id ORDER BY date)""")

def past_features(y, prices, date, meta, calendar):
    """Only the values supplied in y are used; recursive callers append predictions."""
    f=dict(meta);f.update(calendar);n=len(y)
    for k in LAGS: f[f'lag_{k}']=float(y[-k]) if n>=k else np.nan
    for k in [7,28,56]:
        f[f'rolling_mean_{k}']=float(np.mean(y[-k:]))
        if k<56: f[f'rolling_std_{k}']=float(np.std(y[-k:],ddof=1)) if n>1 else 0.
    positives=np.flatnonzero(np.asarray(y)>0)
    f['days_since_last_sale']=n-int(positives[-1]) if len(positives) else np.nan
    # Future price is frozen at origin, including every backtest fold.
    f['sell_price']=prices[-1];f['price_change_percentage']=0.
    f.update(weekday=(date.dayofweek+1)%7,week=int(date.isocalendar().week),month=date.month,quarter=date.quarter)
    return f

def encode(frame, levels=None):
    x=frame[FEATURES].copy()
    if levels is None: levels={c:sorted(frame[c].fillna('Unknown').astype(str).unique()) for c in CATEGORICAL}
    for c in CATEGORICAL: x[c]=pd.Categorical(x[c].fillna('Unknown').astype(str),categories=levels[c])
    for c in NUMERIC: x[c]=pd.to_numeric(x[c],errors='coerce')
    return x,levels
