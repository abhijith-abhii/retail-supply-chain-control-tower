import math
import numpy as np
import pandas as pd
from src.inventory.calculate_inventory_policy import round_order

def simulate_series(actual,forecast,dates,p,policy,seed,run_id,baseline_days_cover=14,scenario='base'):
    """Lost-sales simulation. Receive -> demand -> review/order; arrivals >= tomorrow.
    A common random lead-time draw is indexed by calendar day across policies.
    """
    rng=np.random.default_rng(seed)
    lead_times=np.maximum(1,np.rint(rng.normal(p['average_lead_time_days'],p['lead_time_standard_deviation'],len(actual))).astype(int))
    on_hand=float(p['initial_inventory']);pipeline=[];rows=[];cycle_loss=False;cycle_started=False
    for day,(demand,pred,date) in enumerate(zip(actual,forecast,dates)):
        opening=on_hand;arrivals=sum(q for t,q in pipeline if t==day)
        # Complete an actual replenishment cycle only upon a receipt; do not count unfinished cycles.
        completed=int(arrivals>0 and cycle_started);successful=int(completed and not cycle_loss)
        if arrivals>0: cycle_loss=False;cycle_started=True
        pipeline=[(t,q) for t,q in pipeline if t>day];on_hand+=arrivals
        fulfilled=min(on_hand,float(demand));lost=float(demand)-fulfilled;on_hand-=fulfilled
        cycle_loss=cycle_loss or lost>0;in_transit=sum(q for _,q in pipeline);position=on_hand+in_transit;order=0
        if day % int(p['review_period_days'])==0:
            if policy=='baseline':
                target=p['average_daily_demand']*baseline_days_cover
                order=round_order(target-position,p['minimum_order_quantity'],p['case_pack_size'])
            else:
                # Rolling future forecast protection window, padded with terminal daily forecast.
                protection=int(math.ceil(p['average_lead_time_days']+p['review_period_days']))
                future=np.asarray(forecast[day+1:day+1+protection],float)
                target=float(future.sum()+(protection-len(future))*forecast[-1])+p['protection_safety_stock']
                if position<target:
                    order=round_order(max(p['eoq'],target-position),p['minimum_order_quantity'],p['case_pack_size'])
            if order: pipeline.append((day+int(lead_times[day]),order))
        holding=on_hand*p['estimated_unit_cost']*p['annual_holding_cost_rate']/365
        ordering=p['ordering_cost_per_order'] if order else 0.;lost_cost=lost*p['lost_sale_penalty']
        rows.append(dict(item_id=p['item_id'],store_id=p['store_id'],date=date,policy=policy,scenario=scenario,
         run_id=run_id,target_service_level=p['target_service_level'],opening_inventory=opening,arrivals=arrivals,
         forecast_demand=float(pred),actual_demand=float(demand),fulfilled_units=fulfilled,lost_sales_units=lost,
         order_quantity=order,in_transit_units=sum(q for _,q in pipeline),closing_inventory=on_hand,
         stockout_event=int(lost>0),holding_cost=holding,ordering_cost=ordering,lost_sale_cost=lost_cost,
         total_inventory_cost=holding+ordering+lost_cost,lost_sales_value=lost*p['last_price'],
         estimated_unit_cost=p['estimated_unit_cost'],completed_cycles=completed,successful_cycles=successful))
    return pd.DataFrame(rows)

def simulate(test,policies,cfg,scenario='base'):
    rows=[]
    for idx,((item,store),g) in enumerate(test.groupby(['item_id','store_id'],sort=True)):
        g=g.sort_values('date')
        for p in policies[(policies.item_id==item)&(policies.store_id==store)].to_dict('records'):
            for run in range(cfg['inventory']['monte_carlo_runs']):
                for policy in ['baseline','optimized']:
                    rows.append(simulate_series(g.actual_units.to_numpy(),g.forecast_units.to_numpy(),g.date,p,policy,
                     cfg['seed']+idx*10000+run,run,cfg['inventory']['baseline_days_cover'],scenario))
    daily=pd.concat(rows,ignore_index=True)
    return daily,summarize(daily)

def summarize(daily):
    keys=['item_id','store_id','policy','scenario','target_service_level','run_id']
    k=daily.groupby(keys).agg(actual_demand=('actual_demand','sum'),fulfilled_units=('fulfilled_units','sum'),lost_sales_units=('lost_sales_units','sum'),
      lost_sales_value=('lost_sales_value','sum'),average_inventory=('closing_inventory','mean'),maximum_inventory=('closing_inventory','max'),
      stockout_days=('stockout_event','sum'),holding_cost=('holding_cost','sum'),ordering_cost=('ordering_cost','sum'),
      lost_sale_cost=('lost_sale_cost','sum'),total_inventory_cost=('total_inventory_cost','sum'),
      completed_cycles=('completed_cycles','sum'),successful_cycles=('successful_cycles','sum'),days=('date','size')).reset_index()
    k['fill_rate']=k.fulfilled_units.div(k.actual_demand.replace(0,np.nan))
    k['cycle_service_level']=k.successful_cycles.div(k.completed_cycles.replace(0,np.nan))
    k['inventory_turnover']=k.fulfilled_units.div(k.average_inventory.replace(0,np.nan))*365/k.days
    join=['item_id','store_id','scenario','target_service_level','run_id']
    b=k[k.policy=='baseline'][join+['total_inventory_cost','lost_sales_value']].rename(columns={'total_inventory_cost':'baseline_cost','lost_sales_value':'baseline_lost_sales_value'})
    k=k.merge(b,on=join,validate='many_to_one')
    k['estimated_cost_reduction']=k.baseline_cost-k.total_inventory_cost
    k['estimated_revenue_protected']=k.baseline_lost_sales_value-k.lost_sales_value
    return k
