from pathlib import Path
import json
import pandas as pd
from src.utils.file_utils import write_json

def write_reports(out,reports,mode,fixture,champion,comparison,test,kpis,shipping,policy):
    reports=Path(reports);reports.mkdir(parents=True,exist_ok=True)
    label='SYNTHETIC FIXTURE — engineering validation only' if fixture else 'Kaggle source data — selected cohort' if mode=='sample' else 'Kaggle source data — full cohort'
    best=comparison[(comparison.split_role=='test')&(comparison.model==champion)&(comparison.forecast_level=='item_store')].iloc[0]
    service=.95
    k=kpis[(kpis.target_service_level==service)&(kpis.policy=='optimized')]
    cost=k.groupby('run_id').total_inventory_cost.sum().mean();saving=k.groupby('run_id').estimated_cost_reduction.sum().mean()
    ship=shipping[shipping.dimension=='shipping_mode'].sort_values('late_delivery_rate',ascending=False)
    worst=ship.iloc[0]
    risk=policy[policy.target_service_level==service].sort_values('stockout_probability',ascending=False).iloc[0]
    text=f"""# Executive evidence report

Data provenance: **{label}**. Forecasts are estimates; inventory economics are simulated scenario estimates.
No savings represent measured operational changes. M5 and DataCo are independent domains.

## Forecast evidence
Selected model: `{champion}` using the pre-test selection fold. Held-out WAPE: {best.wape:.2%}; MAE: {best.mae:.3f}; normalized bias: {best.bias:.2%}.
Empirical held-out interval coverage: 80% band {test.covered_80.mean():.2%}; 95% band {test.covered_95.mean():.2%}.
Source: `forecast_model_metrics`, `forecast_backtest_selected`.

## Inventory scenario evidence
At 95% target service, optimized average total cost across runs: {cost:,.2f} currency units.
Baseline minus optimized cost: {saving:,.2f} currency units (negative means optimized costs more).
Source: `inventory_simulation_kpis`; preserve service level and average across runs before aggregation.
Highest modeled starting-stock risk: {risk.item_id}/{risk.store_id}, probability {risk.stockout_probability:.2%}.
Source: `stockout_risk`; assumes no initial purchase orders and simulated opening inventory.
Recommendation: verify lead times and opening stock for this pair before applying its replenishment recommendation.

## Logistics evidence
Shipping mode with largest observed late share: {worst.segment}, {worst.late_orders:,.0f}/{worst.eligible_orders:,.0f} eligible orders ({worst.late_delivery_rate:.2%}).
Source: `dataco_shipping_mode_performance`. Investigate capacity and promise-setting; association does not establish cause.

## Decision gates
Pilot inventory changes only after validating real procurement costs, inventory positions and supplier distributions.
Evaluate profit and service trade-offs across `inventory_sensitivity`; do not select a policy solely for lower stockouts.
Review sparse segments and uncertainty before stocking for event-associated uplift. SNAP is benefit eligibility, not a promotion flag.
If this report uses fixtures, every observation above describes the synthetic fixture only and is not a business finding.
"""
    (reports/'executive_summary.md').write_text(text)
    (reports/'model_performance.md').write_text('# Model performance\n\n'+label+'\n\n'+comparison.to_csv(index=False)+'\nRMSSE is pooled normalized squared error at bottom level, not official hierarchical WRMSSE. Aggregate ETS/SARIMA rows are a separate forecast level and are not candidates for item-store replenishment.\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    trend=test.groupby('date')[['actual_units','forecast_units','lower_80','upper_80']].sum()
    fig,ax=plt.subplots(figsize=(11,4));ax.plot(trend.index,trend.actual_units,label='Actual');ax.plot(trend.index,trend.forecast_units,label='Forecast')
    ax.set(title=label+' | held-out demand',ylabel='Units');ax.legend();fig.autofmt_xdate();fig.tight_layout();fig.savefig(reports/'forecast_validation.png',dpi=160);plt.close(fig)
    import plotly.express as px
    fig=px.bar(comparison[comparison.forecast_level=='item_store'],x='model',y='wape',color='split_role',barmode='group',title=label+' | forecast comparison')
    fig.write_html(reports/'model_comparison.html',include_plotlyjs=True)

def output_dictionary(out,root):
    import pyarrow.parquet as pq
    descriptions={
      'forecast_units':('forecast','Predicted unit demand for date and model; sum only one model/origin'),
      'actual_units':('observed','Held-out recorded sales units, not uncensored demand'),
      'units_sold':('observed','Recorded M5 sales units'),
      'revenue':('derived','Units sold multiplied by weekly selling price; zero when zero units'),
      'sales':('observed','DataCo configured line net sales field; currency per source'),
      'profit':('observed','DataCo configured line benefit field; validate source semantics'),
      'target_service_level':('simulated','Assumed cycle-service probability, not fill rate'),
      'stockout_probability':('simulated','Normal lead-time-demand tail at assumed starting stock'),
      'date_key':('derived','YYYYMMDD integer key'),
      'scale':('derived','Mean squared training first difference after first nonzero sale'),
      'inventory_value':('simulated','Initial units multiplied by estimated unit cost'),
      'rmsse':('derived','Square root of pooled squared error divided by per-series training scale'),
      'bias':('derived','Sum(forecast-actual)/sum(actual); positive is overforecast'),
      'wape':('derived','Sum absolute errors / sum actual; null for zero denominator'),
      'late_order':('derived','Actual shipping duration > scheduled duration; null if ineligible'),
      'delay_days':('derived','Actual minus scheduled shipping duration, signed'),
      'positive_delay_days':('derived','max(delay_days,0), eligible orders only'),
      'run_id':('simulated','Monte Carlo repetition; average costs across runs, never sum repeated worlds'),
      'scenario':('simulated','One-factor-at-a-time assumption scenario'),
      'policy':('simulated','Baseline or forecast-driven optimized replenishment rule'),
      'split_role':('derived','Calibration, selection, or locked test chronological window'),
      'origin':('derived','Last historical date available to the forecast'),
      'item_id':('observed','M5 product natural key'), 'store_id':('observed','M5 store natural key'),
      'date':('observed','Calendar date; forecast dates refer to known future calendar'),
      'order_id':('observed','DataCo business order key; not a customer identifier'),
      'order_item_id':('observed','DataCo unique order-line key'),
    }
    import yaml
    explicit=yaml.safe_load((Path(root)/'config/field_definitions.yaml').read_text())
    descriptions.update({name:(value['provenance'],value['definition']) for name,value in explicit.items()})
    tables={}
    for path in sorted(Path(out).glob('*.parquet')):
        schema=pq.read_schema(path);fields={}
        for f in schema:
            default='simulated' if path.stem.startswith(('inventory','stockout','excess')) else 'derived'
            kind,definition=descriptions.get(f.name,(default,f.name.replace('_',' ').capitalize()+'; see generating module and table grain below.'))
            fields[f.name]={'type':str(f.type),'provenance':kind,'definition':definition}
        tables[path.stem]=fields
    import yaml
    (Path(root)/'config/data_dictionary.yaml').write_text(yaml.safe_dump(tables,sort_keys=False))
    text=['# Output field dictionary','Generated from the executed Parquet schemas. Currency units are source-specific; never add M5 and DataCo money.','Null means unavailable or undefined, never automatically zero. Each forecast has one origin/model; every simulation row includes policy, service, scenario and run.']
    for name,fields in tables.items():
        text+=['\n## '+name,'| Field | Type | Provenance | Definition |','|---|---|---|---|']
        text += [f"| {c} | {v['type']} | {v['provenance']} | {v['definition']} |" for c,v in fields.items()]
    (Path(root)/'docs/data_dictionary.md').write_text('\n'.join(text)+'\n')
