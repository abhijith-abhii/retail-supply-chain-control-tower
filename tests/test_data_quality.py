import pandas as pd
import pytest
from src.validation.schema_validation import required_columns,unique_keys
from src.transformation.transform_dataco import transform_dataco
from src.ingestion.load_dataco import load_dataco,ALLOWED
from src.fixtures import create_fixture
from src.config import load_config

def test_required_columns():
    with pytest.raises(ValueError): required_columns(['a'],['a','b'],'test')
def test_keys():
    with pytest.raises(ValueError): unique_keys(pd.DataFrame({'id':[1,1]}),['id'])
def test_dataco_grain_and_privacy(tmp_path):
    _,dc=create_fixture(tmp_path);cfg=load_config()['dataco']
    raw,_=load_dataco(dc/cfg['filename'],cfg,tmp_path)
    assert set(raw.columns)<=ALLOWED
    lines,orders=transform_dataco(raw,cfg,tmp_path)
    assert len(lines)>len(orders)==240
    assert orders.order_id.is_unique
    assert orders.late_order.dropna().between(0,1).all()
    assert not any('customer_id' in c or 'email' in c or 'password' in c for c in lines)
    assert 'PRIVATE_TEST_NAME' not in lines.to_csv(index=False)
    assert lines.sales.sum()==pytest.approx(raw.order_item_total.sum())
    assert lines.profit.sum()==pytest.approx(raw.benefit_per_order.sum())
def test_conflicting_orders_fail(tmp_path):
    _,dc=create_fixture(tmp_path);cfg=load_config()['dataco'];raw,_=load_dataco(dc/cfg['filename'],cfg,tmp_path)
    order=raw.order_id.value_counts().idxmax();idx=raw.index[raw.order_id==order][0]
    raw.loc[idx,'days_for_shipping_real']=80
    with pytest.raises(ValueError,match='conflicting'): transform_dataco(raw,cfg,tmp_path)
def test_missing_optional_does_not_invent_profit(tmp_path):
    _,dc=create_fixture(tmp_path);cfg=load_config()['dataco'];raw,_=load_dataco(dc/cfg['filename'],cfg,tmp_path)
    lines,_=transform_dataco(raw.drop(columns=['benefit_per_order']),cfg,tmp_path)
    assert lines.profit.isna().all()
