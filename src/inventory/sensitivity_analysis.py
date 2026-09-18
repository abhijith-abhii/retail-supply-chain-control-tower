import pandas as pd
from src.inventory.calculate_inventory_policy import policies
from src.inventory.inventory_simulation import simulate

def sensitivity(history,forecasts,assumptions,errors,test,cfg,origin):
    # One-factor-at-a-time scenarios; same random streams support paired comparisons.
    keys=history.sort_values(['item_id','store_id']).head(cfg['inventory']['sensitivity_series_limit'])[['item_id','store_id']]
    history=history.merge(keys);forecasts=forecasts.merge(keys);assumptions=assumptions.merge(keys);errors=errors.merge(keys);test=test.merge(keys)
    rows=[]
    cases=[('base',None,1)]+[(name+'_'+str(factor),name,factor) for name in ['average_lead_time_days','lead_time_standard_deviation','annual_holding_cost_rate','ordering_cost_per_order','forecast_error','lost_sale_penalty'] for factor in [.5,1.5]]
    for name,col,factor in cases:
        a=assumptions.copy();e=errors.copy()
        if col=='forecast_error': e['error']*=factor
        elif col: a[col]*=factor
        p=policies(history,forecasts,a,e,cfg['inventory']['service_levels'],origin)
        _,k=simulate(test,p,cfg,scenario=name);k['sensitivity_factor']=col or 'none';k['multiplier']=factor;rows.append(k)
    return pd.concat(rows,ignore_index=True)
