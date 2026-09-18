import math
from statistics import NormalDist
import numpy as np
import pandas as pd

def safety_stock(mean,sd,lead,lead_sd,service):
    if not 0<service<1: raise ValueError('Service level must be in (0,1)')
    if min(mean,sd,lead,lead_sd)<0: raise ValueError('Negative demand/lead parameter')
    return NormalDist().inv_cdf(service)*math.sqrt(lead*sd**2+mean**2*lead_sd**2)
def eoq(annual_demand,ordering_cost,annual_holding_per_unit):
    if min(annual_demand,ordering_cost)<0 or annual_holding_per_unit<=0: raise ValueError('Invalid EOQ inputs')
    return math.sqrt(2*annual_demand*ordering_cost/annual_holding_per_unit)
def round_order(q,moq,pack):
    if pack<=0 or moq<0: raise ValueError('Invalid lot constraints')
    return math.ceil(max(q,moq)/pack)*pack if q>0 else 0

def policies(history,forecasts,assumptions,errors,service_levels,as_of):
    means=forecasts.groupby(['item_id','store_id']).forecast_units.mean().rename('forecast_daily_demand')
    err=errors.groupby(['item_id','store_id']).error.std().rename('forecast_error_std')
    x=history.merge(assumptions,on=['item_id','store_id'],validate='one_to_one').merge(means,on=['item_id','store_id'],validate='one_to_one').merge(err,on=['item_id','store_id'],how='left',validate='one_to_one')
    rows=[]
    for r in x.to_dict('records'):
        for field in ['estimated_unit_cost','annual_holding_cost_rate','case_pack_size','review_period_days','average_lead_time_days']:
            if pd.isna(r[field]) or r[field]<=0: raise ValueError('Invalid assumption: '+field)
        for field in ['initial_inventory','lead_time_standard_deviation','ordering_cost_per_order','lost_sale_penalty','minimum_order_quantity']:
            if pd.isna(r[field]) or r[field]<0: raise ValueError('Invalid assumption: '+field)
        for level in service_levels:
            p=dict(r);p['target_service_level']=level;p['as_of_date']=pd.Timestamp(as_of)
            mean=r['forecast_daily_demand'];sd=r['forecast_error_std']
            if pd.isna(sd): sd=r['demand_std']
            L=r['average_lead_time_days'];R=r['review_period_days'];ls=r['lead_time_standard_deviation']
            ss=safety_stock(mean,sd,L,ls,level);protection_ss=safety_stock(mean,sd,L+R,ls,level)
            p.update(safety_stock=ss,expected_lead_time_demand=mean*L,reorder_point=mean*L+ss,
              protection_safety_stock=protection_ss,order_up_to_level=mean*(L+R)+protection_ss,
              eoq=eoq(mean*365,r['ordering_cost_per_order'],r['estimated_unit_cost']*r['annual_holding_cost_rate']),
              days_of_supply=r['initial_inventory']/mean if mean else np.nan,
              inventory_value=r['initial_inventory']*r['estimated_unit_cost'],demand_uncertainty_std=sd)
            # Normal lead-time-demand approximation; no incoming POs in assumed starting inventory.
            sigma=math.sqrt(L*sd**2+mean**2*ls**2)
            p['stockout_probability']=1-NormalDist(mean*L,sigma).cdf(r['initial_inventory']) if sigma>0 else float(r['initial_inventory']<mean*L)
            p['recommended_order_quantity']=round_order(max(p['eoq'],p['order_up_to_level']-r['initial_inventory']),r['minimum_order_quantity'],r['case_pack_size']) if r['initial_inventory']<p['order_up_to_level'] else 0
            p['excess_units']=max(0,r['initial_inventory']-p['order_up_to_level']);p['excess_value']=p['excess_units']*r['estimated_unit_cost']
            rows.append(p)
    return pd.DataFrame(rows)
