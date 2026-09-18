"""CLI orchestration. No credentials required for local files; --load-postgres is explicit."""
import sys
from pathlib import Path
if __package__ in (None,''): sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import argparse
import logging
import shutil
import time
import numpy as np
import pandas as pd
import duckdb
from src.config import ROOT,load_config
from src.logging_config import configure_logging
from src.fixtures import create_fixture
from src.ingestion.load_m5 import load_m5
from src.ingestion.load_dataco import load_dataco
from src.validation.data_quality import audit_csv,validate_m5
from src.transformation.transform_m5 import transform_m5
from src.transformation.transform_dataco import transform_dataco
from src.transformation.build_dimensions import build_dimensions
from src.forecasting.feature_engineering import create_feature_view
from src.forecasting.evaluate_models import evaluate_models,add_intervals,segment_metrics
from src.forecasting.train_models import train_global
from src.forecasting.generate_forecasts import predict_origin
from src.inventory.create_assumptions import create_assumptions
from src.inventory.calculate_inventory_policy import policies
from src.inventory.inventory_simulation import simulate
from src.inventory.sensitivity_analysis import sensitivity
from src.operations.delivery_analysis import delivery_summary,category_delivery
from src.operations.profitability_analysis import profitability
from src.analysis import eda,history_summary,segmentation
from src.utils.file_utils import export_frame,write_json,sql_literal
from src.reporting import write_reports,output_dictionary

def run(mode='sample',fixture=False,root=ROOT,config_path=None,load_postgres=False,skip_audit=False):
    root=Path(root);cfg=load_config(config_path);started=time.perf_counter();configure_logging()
    tag='fixture' if fixture else mode
    out=root/'data/powerbi'/tag;processed=root/'data/processed'/tag;reports=root/'reports'/tag
    for p in [out,processed,reports,root/'data/interim']: p.mkdir(parents=True,exist_ok=True)
    # Rebuild only owned generated run directories, avoiding stale partition mixing.
    if processed.exists(): shutil.rmtree(processed)
    processed.mkdir(parents=True)
    for p in out.glob('*.parquet'): p.unlink()
    for p in out.glob('*.csv'): p.unlink()
    m5,dc=create_fixture(root/'data/sample',cfg['seed']) if fixture else (root/'data/raw/m5',root/'data/raw/dataco')
    con=duckdb.connect(str(root/'data/interim'/f'{tag}.duckdb'))
    con.execute(f"SET threads={int(cfg['threads'])}");con.execute(f"SET memory_limit={sql_literal(cfg['duckdb_memory_limit'])}")
    logging.info('Loading and validating source files')
    load_m5(con,m5);validate_m5(con)
    raw_dataco,encoding=load_dataco(dc/cfg['dataco']['filename'],cfg['dataco'],reports)
    if not skip_audit:
        for path in sorted(m5.glob('*.csv')): audit_csv(path,reports)
        audit_csv(dc/cfg['dataco']['filename'],reports,encoding)
    cohort_cutoff=transform_m5(con,cfg,mode,processed/'sales_daily')
    create_feature_view(con)
    history_days=con.execute('SELECT min(n) FROM (SELECT count(*) n FROM sales GROUP BY item_id,store_id)').fetchone()[0]
    needed=max(28,cfg['inventory']['simulation_days'])*cfg['backtest_folds']+cfg['minimum_history_days']
    if history_days<needed: raise ValueError(f'Need at least {needed} daily observations per series')
    # Large sales exports stream through DuckDB, not Pandas.
    con.execute(f"COPY sales TO {sql_literal(out/'sales_daily.parquet')} (FORMAT PARQUET)")
    con.execute(f"COPY features TO {sql_literal(processed/'forecast_features.parquet')} (FORMAT PARQUET)")
    lines,delivery=transform_dataco(raw_dataco,cfg['dataco'],reports)
    export_frame(lines,'dataco_profitability',out);export_frame(delivery,'dataco_delivery_performance',out)
    ship=delivery_summary(delivery);export_frame(ship,'dataco_shipping_mode_performance',out)
    export_frame(category_delivery(lines,delivery),'dataco_category_delivery',out)
    profit,orders=profitability(lines);export_frame(profit,'dataco_profitability_summary',out);export_frame(orders,'dataco_order_profit',out)
    dims=build_dimensions(con,lines,delivery,out);tables=eda(con,lines,delivery,cfg,out)
    logging.info('Rolling-origin model comparison')
    backtest,comparison,test,champion=evaluate_models(con,cfg)
    export_frame(backtest,'forecast_backtest_all',out);export_frame(test,'forecast_backtest_selected',out)
    export_frame(comparison,'forecast_model_metrics',out)
    # Segment labels are frozen at final test origin, never recomputed with held-out demand.
    test_origin=test.origin.iloc[0];pretest=history_summary(con,test_origin)
    export_frame(segment_metrics(test,segmentation(pretest,cfg)),'forecast_accuracy_by_segment',out)
    end=con.execute('SELECT max(date) FROM sales').fetchone()[0]
    model,levels,_=train_global(con,end,cfg) if champion=='lightgbm' else (None,None,0)
    future=predict_origin(con,end,28,[champion],cfg,model,levels)
    selected_errors=backtest[(backtest.model==champion)&(backtest.fold<cfg['backtest_folds'])]
    future=add_intervals(future,selected_errors);export_frame(future,'demand_forecasts_28d',out)
    logging.info('Calculating simulated inventory policies and paired replenishment scenarios')
    current=history_summary(con,end);assumptions=create_assumptions(current,cfg)
    # Preserve user-supplied real-run assumptions; fixture never reads real assumption files.
    assumption_path=root/'config/inventory_assumptions.csv'
    if not fixture and assumption_path.exists():
        supplied=pd.read_csv(assumption_path)
        if len(supplied):
            if supplied.duplicated(['item_id','store_id']).any(): raise ValueError('Duplicate inventory assumptions')
            assumptions=assumptions.set_index(['item_id','store_id'])
            supplied=supplied.set_index(['item_id','store_id']);assumptions.update(supplied);assumptions=assumptions.reset_index()
    if not fixture: assumptions.to_csv(assumption_path,index=False)
    export_frame(assumptions,'inventory_assumptions',out)
    policy=policies(current,future,assumptions,selected_errors,cfg['inventory']['service_levels'],end)
    export_frame(policy,'inventory_policy_recommendations',out)
    export_frame(policy,'stockout_risk',out);export_frame(policy[policy.excess_units>0],'excess_inventory',out)
    # Historical evaluation recreates assumptions at its origin; no future prices or demand used.
    sim_assumptions=create_assumptions(pretest,cfg)
    sim_policy=policies(pretest,test,sim_assumptions,selected_errors,cfg['inventory']['service_levels'],test_origin)
    limit=cfg['inventory'].get('simulation_series_limit',100)
    sim_keys=pretest.sort_values(['item_id','store_id']).head(limit)[['item_id','store_id']]
    sim_test=test.merge(sim_keys);sim_policy=sim_policy.merge(sim_keys)
    daily,kpis=simulate(sim_test,sim_policy,cfg)
    export_frame(daily,'inventory_simulation_daily',out);export_frame(kpis,'inventory_simulation_kpis',out)
    sens=sensitivity(pretest,test,sim_assumptions,selected_errors,sim_test,cfg,test_origin)
    export_frame(sens,'inventory_sensitivity',out)
    # Executive metrics remain separately labelled, with compatible denominators.
    observed=con.execute('SELECT sum(units_sold) units,sum(revenue) revenue FROM sales').fetchone()
    k=kpis[(kpis.policy=='optimized')&(kpis.target_service_level==cfg['inventory']['default_service_level'])]
    exec_rows=[('M5','historical','total_units',observed[0]),('M5','historical','revenue',observed[1]),('M5','forecast','forecast_28d_units',future.forecast_units.sum()),
      ('M5','scenario_estimate','estimated_cost_reduction',k.groupby('run_id').estimated_cost_reduction.sum().mean()),
      ('DataCo','historical','eligible_order_late_rate',delivery.loc[delivery.delivery_eligible,'late_order'].mean()),('DataCo','historical','profit',orders.profit.sum(min_count=1))]
    executive=pd.DataFrame(exec_rows,columns=['domain','metric_type','metric','value']);executive['data_provenance']='synthetic_fixture' if fixture else 'kaggle'
    export_frame(executive,'executive_kpis',out)
    if cfg['dataco']['risk_model']:
        from src.operations.delivery_risk_model import delivery_risk
        risk,importance=delivery_risk(delivery,cfg['seed']);export_frame(risk,'delivery_risk_metrics',out);export_frame(importance,'delivery_risk_feature_importance',out)
    export_frame(pd.DataFrame({'last_refresh_utc':[pd.Timestamp.now(tz='UTC').isoformat()],'data_provenance':['synthetic_fixture' if fixture else 'kaggle'],'mode':[mode]}),'refresh_metadata',out)
    from src.recommendations import recommendations
    export_frame(recommendations(out,fixture),'recommendations',out)
    write_reports(out,reports,mode,fixture,champion,comparison,test,kpis,ship,policy);output_dictionary(out,root)
    if load_postgres:
        from src.database import load_database
        load_database(out,root/'sql')
    manifest={'mode':mode,'fixture':fixture,'selected_model':champion,'cohort_selection_cutoff':str(cohort_cutoff),'postgres_loaded':load_postgres,
      'source_sales_rows':con.execute('SELECT count(*) FROM sales').fetchone()[0], 'forecast_rows':len(future),'simulation_series':len(sim_keys),
      'audits_executed':not skip_audit,'elapsed_seconds':time.perf_counter()-started,'output_dir':str(out),'config':cfg}
    write_json(reports/'run_manifest.json',manifest);con.close();logging.info('Pipeline complete: %s',out)
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['sample','full'],default='sample');p.add_argument('--fixture',action='store_true');p.add_argument('--config');p.add_argument('--load-postgres',action='store_true');p.add_argument('--skip-audit',action='store_true',help='Explicit development-only bypass; recorded in manifest')
    args=p.parse_args();run(args.mode,args.fixture,config_path=args.config,load_postgres=args.load_postgres,skip_audit=args.skip_audit)
