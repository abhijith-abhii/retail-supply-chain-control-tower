import numpy as np
import pandas as pd
from src.forecasting.feature_engineering import past_features,encode
from src.forecasting.baselines import baseline
from src.utils.metrics import rmsse_scale

def predict_origin(con,origin,horizon,names,cfg,model=None,levels=None):
    origin=pd.Timestamp(origin)
    keys=con.execute('SELECT DISTINCT item_id,store_id FROM sales ORDER BY item_id,store_id').df()
    cal=con.execute('SELECT * FROM calendar WHERE cast(date AS DATE)>? AND cast(date AS DATE)<=?',[origin,origin+pd.Timedelta(days=horizon)]).df()
    cal['date']=pd.to_datetime(cal.date);cal=cal.set_index('date')
    if len(cal)!=horizon: raise ValueError('Calendar must cover every forecast date; add an explicit known-future calendar')
    rows=[]
    for start in range(0,len(keys),cfg['prediction_batch_series']):
        batch=keys.iloc[start:start+cfg['prediction_batch_series']];con.register('batch_keys',batch)
        history=con.execute('SELECT s.* FROM sales s JOIN batch_keys USING(item_id,store_id) WHERE date<=? ORDER BY item_id,store_id,date',[origin]).df()
        con.unregister('batch_keys')
        states=[]
        for (item,store),g in history.groupby(['item_id','store_id'],sort=True):
            meta=g.iloc[-1].to_dict();y=g.units_sold.to_numpy(float);prices=g.sell_price.dropna().to_list()
            if not prices: raise ValueError(f'No known price for {item}/{store}')
            meta['scale']=rmsse_scale(y)
            states.append((item,store,meta,y.tolist(),prices))
            for name in names:
                if name=='lightgbm': continue
                for h,pred in enumerate(baseline(y,horizon,name),1):
                    rows.append(record(meta,item,store,origin,h,name,pred))
        if 'lightgbm' in names:
            for h in range(1,horizon+1):
                date=origin+pd.Timedelta(days=h);c=cal.loc[date];features=[]
                for item,store,meta,y,prices in states:
                    known={'event_flag':int(pd.notna(c.get('event_name_1')) or pd.notna(c.get('event_name_2'))),
                     'event_type':c.get('event_type_1'),'snap_flag':c['snap_'+meta['state_id']]}
                    features.append(past_features(y,prices,date,meta,known))
                x,_=encode(pd.DataFrame(features),levels);preds=np.maximum(0,model.predict(x))
                for state,pred in zip(states,preds):
                    item,store,meta,y,prices=state;y.append(float(pred))
                    rows.append(record(meta,item,store,origin,h,'lightgbm',pred))
    return pd.DataFrame(rows)

def record(meta,item,store,origin,h,name,pred):
    date=origin+pd.Timedelta(days=h)
    return dict(item_id=item,store_id=store,state_id=meta['state_id'],category_id=meta['category_id'],
     department_id=meta['department_id'],origin=origin,date=date,date_key=int(date.strftime('%Y%m%d')),
     horizon=h,model=name,forecast_units=float(pred),scale=meta['scale'])
