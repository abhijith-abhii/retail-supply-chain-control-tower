from pathlib import Path
import json
import os
import pandas as pd
import pytest
from src.config import ROOT,load_config
from src.ingestion.load_m5 import detect_sales

REQUIRED=['sales_daily','sales_monthly','product_store_performance','demand_forecasts_28d','forecast_model_metrics','forecast_accuracy_by_segment','inventory_assumptions','inventory_policy_recommendations','inventory_simulation_daily','inventory_simulation_kpis','abc_xyz_segmentation','stockout_risk','excess_inventory','dataco_delivery_performance','dataco_shipping_mode_performance','dataco_profitability','executive_kpis']

def test_sales_file_precedence(tmp_path):
    (tmp_path/'sales_train_validation.csv').touch();assert 'validation' in detect_sales(tmp_path).name
    (tmp_path/'sales_train_evaluation.csv').touch();assert 'evaluation' in detect_sales(tmp_path).name

def test_executed_fixture_outputs():
    out=ROOT/'data/powerbi/fixture'
    assert out.exists(),'Run make demo before integration tests'
    for name in REQUIRED: assert (out/(name+'.parquet')).exists(),name
    f=pd.read_parquet(out/'demand_forecasts_28d.parquet')
    assert f.groupby(['item_id','store_id']).size().eq(28).all()
    assert (f.date-f.origin).dt.days.equals(f.horizon)
    assert f.forecast_units.ge(0).all()
    assert (f.lower_95<=f.lower_80).all() and (f.upper_95>=f.upper_80).all()
    s=pd.read_parquet(out/'sales_daily.parquet');p=pd.read_parquet(out/'dim_product.parquet');d=pd.read_parquet(out/'dim_date.parquet')
    assert p.item_id.is_unique and d.date_key.is_unique
    assert set(s.item_id)<=set(p.item_id) and set(f.date_key)<=set(d.date_key)
    assert s.units_sold.ge(0).all() and s.sell_price.dropna().ge(0).all()
    inv=pd.read_parquet(out/'inventory_policy_recommendations.parquet')
    assert ((inv.reorder_point-inv.expected_lead_time_demand-inv.safety_stock).abs()<1e-8).all()
    for path in out.glob('*.parquet'):
        import pyarrow.parquet as pq
        cols=pq.read_schema(path).names
        assert not any(c in cols for c in ['customer_email','customer_password','customer_fname','customer_id','customer_street','phone'])

def test_postgres_integration():
    if not os.getenv('TEST_DATABASE_URL'): pytest.skip('Set TEST_DATABASE_URL for a dedicated disposable PostgreSQL database')
    from src.database import load_database
    os.environ['DATABASE_URL']=os.environ['TEST_DATABASE_URL']
    load_database(ROOT/'data/powerbi/fixture',ROOT/'sql')
