import math
import numpy as np
import pandas as pd
import pytest
from statistics import NormalDist
from src.inventory.calculate_inventory_policy import safety_stock,eoq,round_order,policies
from src.inventory.inventory_simulation import simulate_series,summarize

def test_safety_stock():
    assert safety_stock(10,3,7,2,.95)==pytest.approx(NormalDist().inv_cdf(.95)*math.sqrt(7*9+100*4))
@pytest.mark.parametrize('level',[0,1,-.1,1.1])
def test_service_guard(level):
    with pytest.raises(ValueError): safety_stock(10,3,7,2,level)
def test_eoq_and_rounding():
    assert eoq(1200,25,3)==pytest.approx(math.sqrt(20000))
    assert round_order(7,6,6)==12
    assert round_order(0,6,6)==0

def test_balance_arrivals_and_fill():
    p=dict(item_id='a',store_id='s',initial_inventory=10,average_lead_time_days=2,lead_time_standard_deviation=0,
     review_period_days=1,average_daily_demand=5,minimum_order_quantity=6,case_pack_size=6,protection_safety_stock=4,
     eoq=12,estimated_unit_cost=2,annual_holding_cost_rate=.25,ordering_cost_per_order=10,lost_sale_penalty=3,last_price=4,target_service_level=.95)
    x=simulate_series(np.repeat(5,10),np.repeat(5,10),pd.date_range('2020-01-01',periods=10),p,'baseline',42,0)
    np.testing.assert_allclose(x.opening_inventory+x.arrivals-x.fulfilled_units,x.closing_inventory)
    np.testing.assert_allclose(x.actual_demand,x.fulfilled_units+x.lost_sales_units)
    assert x.arrivals.iloc[0]==x.arrivals.iloc[1]==0
    assert (x.order_quantity%6==0).all()
    k=summarize(x);assert k.fill_rate.between(0,1).all()
