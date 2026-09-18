import time
import pandas as pd
from lightgbm import LGBMRegressor
from src.forecasting.feature_engineering import encode

def train_global(con,origin,cfg):
    start=time.perf_counter()
    # Deterministic row cap permits bounded training memory even for full M5.
    train=con.execute(f"""SELECT * FROM features WHERE date<=? AND
      date>? - INTERVAL '{cfg['training_days']} days' AND lag_56 IS NOT NULL
      ORDER BY hash(item_id,store_id,date,{int(cfg['seed'])}) LIMIT {int(cfg['max_training_rows'])}""",[origin,origin]).df()
    if train.empty: raise ValueError('Not enough training history for lag_56')
    x,levels=encode(train)
    model=LGBMRegressor(n_estimators=120,num_leaves=31,learning_rate=.05,objective='poisson',
        random_state=cfg['seed'],n_jobs=cfg['threads'],deterministic=True,force_col_wise=True,verbosity=-1)
    model.fit(x,train.units_sold)
    return model,levels,time.perf_counter()-start

def aggregate_statistical(con,origin,horizon):
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    y=con.execute('SELECT date,sum(units_sold) y FROM sales WHERE date<=? GROUP BY date ORDER BY date',[origin]).df().set_index('date').y.asfreq('D')
    result=[]
    for name,factory in [('ets',lambda:ExponentialSmoothing(y,trend='add',seasonal='add',seasonal_periods=7,initialization_method='estimated').fit()),
                         ('sarima',lambda:SARIMAX(y,order=(1,0,0),seasonal_order=(1,0,0,7),enforce_stationarity=False).fit(disp=False,maxiter=100))]:
        t=time.perf_counter();fit=factory()
        result.append((name,fit.forecast(horizon).clip(lower=0).to_numpy(),time.perf_counter()-t))
    return result
