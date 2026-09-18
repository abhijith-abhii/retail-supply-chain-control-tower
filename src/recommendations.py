"""Recommendations quote calculated evidence and never imply causal or achieved impact."""
from pathlib import Path
import pandas as pd

def recommendations(out, fixture):
    out=Path(out);read=lambda n:pd.read_parquet(out/(n+'.parquet'));rows=[]
    provenance='synthetic_fixture' if fixture else 'kaggle'
    def emit(domain,kind,action,evidence,source): rows.append(dict(domain=domain,evidence_type=kind,recommendation=action,evidence=evidence,source_table=source,data_provenance=provenance))
    policy=read('inventory_policy_recommendations').query('target_service_level == 0.95')
    r=policy.sort_values('stockout_probability',ascending=False).iloc[0]
    emit('M5','scenario','Verify starting stock and consider a larger buffer for '+r.item_id+'/'+r.store_id,f'Modeled stockout probability {r.stockout_probability:.4f}; safety stock {r.safety_stock:.2f} units','inventory_policy_recommendations')
    excess=policy.sort_values('excess_value',ascending=False)
    if len(excess) and excess.iloc[0].excess_value>0:
        r=excess.iloc[0];emit('M5','scenario','Review lower replenishment for '+r.item_id+'/'+r.store_id,f'Assumed excess {r.excess_units:.2f} units; value {r.excess_value:.2f}','inventory_policy_recommendations')
    accuracy=read('forecast_accuracy_by_segment').query("segment_type == 'store_id'").sort_values('wape',ascending=False)
    r=accuracy.iloc[0];emit('M5','forecast_evaluation','Prioritize forecast-error review in store '+r.segment,f'Locked-test WAPE {r.wape:.4f}','forecast_accuracy_by_segment')
    perf=read('product_store_performance');z=perf[perf.xyz=='Z']
    if len(z): emit('M5','historical','Evaluate intermittent-demand methods for Z items',f'{len(z)} item-store pairs classified Z of {len(perf)}; cutoff zero-share 0.5 or configured high CV','product_store_performance')
    cat=policy.groupby('category_id').safety_stock.mean().sort_values(ascending=False)
    emit('M5','scenario','Review separate inventory buffers for category '+str(cat.index[0]),f'Mean safety stock {cat.iloc[0]:.2f} units at 95% assumed service','inventory_policy_recommendations')
    ev=read('m5_by_event_name').dropna(subset=['event_name']).sort_values('mean_series_day_units',ascending=False)
    if len(ev):
        r=ev.iloc[0];emit('M5','historical','Review event calendar ahead of '+r.event_name,f'Observed mean {r.mean_series_day_units:.3f} units per series-day across {r.series_days} observations; unadjusted for seasonality','m5_by_event_name')
    ship=read('dataco_shipping_mode_performance')
    for dim in ['shipping_mode','market']:
        z=ship[ship.dimension==dim].dropna(subset=['late_delivery_rate']).sort_values('late_delivery_rate',ascending=False)
        if len(z):
            r=z.iloc[0];emit('DataCo','historical','Investigate promise-setting and capacity for '+str(r.segment),f'{r.late_orders}/{r.eligible_orders} eligible orders late ({r.late_delivery_rate:.4f}); association only','dataco_shipping_mode_performance')
    profits=read('dataco_profitability_summary').query("dimension == 'category'")
    if profits.sales.notna().any():
        top=profits[profits.sales>=profits.sales.quantile(.75)].sort_values('profit_margin')
        if len(top):
            r=top.iloc[0];emit('DataCo','historical','Review pricing, mix and discount leakage for '+r.segment,f'Top-quartile category sales {r.sales:.2f}; margin {r.profit_margin:.4f}; no causal attribution','dataco_profitability_summary')
    k=read('inventory_simulation_kpis').query("policy == 'optimized'")
    for service,g in k.groupby('target_service_level'):
        savings=g.groupby('run_id').estimated_cost_reduction.sum().mean()
        fill=g.fulfilled_units.sum()/g.actual_demand.sum() if g.actual_demand.sum() else float('nan')
        emit('M5','scenario',f'Compare cost/service before adopting the {service:.0%} target',f'Paired estimated cost reduction {savings:.2f}; demand-weighted fill rate {fill:.4f}; negative savings indicate higher cost','inventory_simulation_kpis')
    return pd.DataFrame(rows)
