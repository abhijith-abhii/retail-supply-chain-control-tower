import numpy as np
import pandas as pd
import duckdb
import pytest
from src.forecasting.feature_engineering import create_feature_view,past_features
from src.forecasting.baselines import baseline
from src.utils.metrics import rmsse_scale,metrics

def features(values):
    n=len(values)
    x=pd.DataFrame({'item_id':'a','store_id':'s','date':pd.date_range('2020-01-01',periods=n),'units_sold':values,'revenue':values,'sell_price':1.})
    con=duckdb.connect();con.register('sales',x);create_feature_view(con)
    result=con.execute('SELECT * FROM features ORDER BY date').df();con.close();return result

def test_future_and_current_perturbation_do_not_change_past_features():
    y=np.arange(1.,81.);before=features(y);y[60:]=99999;after=features(y)
    cols=['lag_1','lag_7','lag_28','rolling_mean_7','rolling_std_28','days_since_last_sale']
    pd.testing.assert_frame_equal(before.loc[:60,cols],after.loc[:60,cols])
    assert before.loc[60,'rolling_mean_7']==np.mean(np.arange(54.,61.))
def test_series_seasonal_pattern():
    assert baseline([1,2,3,4,5,6,7],10,'seasonal_7').tolist()==[1,2,3,4,5,6,7,1,2,3]
def test_metrics_zero_handling_and_scale():
    assert np.isnan(metrics([0,0],[1,1])['wape'])
    assert rmsse_scale([0,0,1,2,4])==pytest.approx(2.5)
    assert np.isnan(rmsse_scale([1,1,1]))

def test_recursive_predictions_ignore_heldout_actuals():
    from src.config import ROOT,load_config
    from src.forecasting.train_models import train_global
    from src.forecasting.generate_forecasts import predict_origin
    from src.ingestion.load_m5 import load_m5
    x=pd.read_parquet(ROOT/'data/powerbi/fixture/sales_daily.parquet')
    x=x[x.item_id==x.item_id.iloc[0]].copy()
    con=duckdb.connect();con.register('input_sales',x);con.execute('CREATE TABLE sales AS SELECT * FROM input_sales')
    cal=pd.read_csv(ROOT/'data/sample/m5/calendar.csv');con.register('calendar',cal)
    create_feature_view(con);origin=x.date.max()-pd.Timedelta(days=28);cfg=load_config()
    m,levels,_=train_global(con,origin,cfg)
    a=predict_origin(con,origin,7,['lightgbm'],cfg,m,levels)
    con.execute('UPDATE sales SET units_sold=units_sold+10000 WHERE date>?',[origin])
    b=predict_origin(con,origin,7,['lightgbm'],cfg,m,levels)
    pd.testing.assert_frame_equal(a,b);con.close()
