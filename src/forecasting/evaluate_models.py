import numpy as np
import pandas as pd
from src.forecasting.baselines import MODELS
from src.forecasting.train_models import train_global,aggregate_statistical
from src.forecasting.generate_forecasts import predict_origin
from src.utils.metrics import metrics

def evaluate_models(con,cfg):
    end=pd.Timestamp(con.execute('SELECT max(date) FROM sales').fetchone()[0])
    h=max(28,cfg['inventory']['simulation_days']);folds=cfg['backtest_folds']
    records=[];comparisons=[]
    champion=None
    for fold in range(1,folds+1):
        origin=end-pd.Timedelta(days=(folds-fold+1)*h)
        model,levels,seconds=train_global(con,origin,cfg)
        pred=predict_origin(con,origin,h,MODELS,cfg,model,levels)
        actual=con.execute('SELECT item_id,store_id,date,units_sold actual_units FROM sales WHERE date>? AND date<=?',[origin,origin+pd.Timedelta(days=h)]).df()
        pred=pred.merge(actual,on=['item_id','store_id','date'],validate='many_to_one')
        pred['fold']=fold;pred['split_role']='calibration' if fold<folds-1 else ('selection' if fold==folds-1 else 'test')
        pred['error']=pred.forecast_units-pred.actual_units;pred['absolute_error']=pred.error.abs();records.append(pred)
        for name,g in pred.groupby('model'):
            comparisons.append(dict(model=name,fold=fold,split_role=g.split_role.iloc[0],origin=origin,
             validation_start=origin+pd.Timedelta(days=1),validation_end=origin+pd.Timedelta(days=h),forecast_level='item_store',
             training_seconds=seconds if name=='lightgbm' else 0.,**metrics(g.actual_units,g.forecast_units,g.scale)))
        aggregate=actual.groupby('date').actual_units.sum()
        for name,p,t in aggregate_statistical(con,origin,h):
            comparisons.append(dict(model=name,fold=fold,split_role=pred.split_role.iloc[0],origin=origin,
             validation_start=origin+pd.Timedelta(days=1),validation_end=origin+pd.Timedelta(days=h),forecast_level='selected_portfolio_total',
             training_seconds=t,**metrics(aggregate,p)))
        if fold==folds-1:
            selection=pd.DataFrame(comparisons).query('fold==@fold and forecast_level=="item_store"')
            champion=selection.sort_values(['wape','mae','model']).model.iloc[0]
    backtest=pd.concat(records,ignore_index=True)
    # Intervals for held-out test use earlier calibration errors only, before model selection/test outcomes.
    calibration=backtest[(backtest.fold<folds-1)&(backtest.model==champion)]
    test=backtest[(backtest.fold==folds)&(backtest.model==champion)].copy()
    test=add_intervals(test,calibration)
    test['covered_80']=(test.actual_units>=test.lower_80)&(test.actual_units<=test.upper_80)
    test['covered_95']=(test.actual_units>=test.lower_95)&(test.actual_units<=test.upper_95)
    return backtest,pd.DataFrame(comparisons),test,champion

def add_intervals(pred,residuals):
    pred=pred.copy()
    # Signed residual actual-prediction, pooled by forecast day. Approximate, not guaranteed coverage.
    for level in [80,95]:
        alpha=(1-level/100)/2
        q=residuals.assign(residual=residuals.actual_units-residuals.forecast_units).groupby('horizon').residual.quantile([alpha,1-alpha]).unstack()
        for label,col in [('lower',0),('upper',1)]:
            shift=pred.horizon.map(q.iloc[:,col]).fillna(float((residuals.actual_units-residuals.forecast_units).quantile([alpha,1-alpha][col])))
            pred[f'{label}_{level}']=(pred.forecast_units+shift).clip(lower=0)
        # Ensure point is displayed inside interval while retaining asymmetric residual bounds.
        pred[f'lower_{level}']=np.minimum(pred[f'lower_{level}'],pred.forecast_units)
        pred[f'upper_{level}']=np.maximum(pred[f'upper_{level}'],pred.forecast_units)
    return pred

def segment_metrics(test,segments):
    x=test.merge(segments[['item_id','store_id','abc_xyz','volume_segment']],on=['item_id','store_id'],validate='many_to_one')
    rows=[]
    for dim in ['state_id','store_id','category_id','department_id','volume_segment','abc_xyz']:
        for val,g in x.groupby(dim): rows.append(dict(segment_type=dim,segment=str(val),model=g.model.iloc[0],**metrics(g.actual_units,g.forecast_units,g.scale)))
    return pd.DataFrame(rows)
