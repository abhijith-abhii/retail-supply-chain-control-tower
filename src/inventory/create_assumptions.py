import numpy as np
import pandas as pd

def create_assumptions(history,cfg):
    a=cfg['inventory'];rng=np.random.default_rng(cfg['seed']);rows=[]
    for r in history.sort_values(['item_id','store_id']).itertuples():
        rows.append(dict(item_id=r.item_id,store_id=r.store_id,supplier_id='SIM_'+r.category_id,
          average_lead_time_days=int(rng.integers(*a['lead_time_days_range'],endpoint=True)),
          lead_time_standard_deviation=a['lead_time_std_days'],ordering_cost_per_order=a['ordering_cost'],
          annual_holding_cost_rate=a['holding_rate'],estimated_unit_cost=max(.01,r.last_price*a['cost_to_price_ratio']),
          target_service_level=a['default_service_level'],initial_inventory=int(np.ceil(r.average_daily_demand*a['initial_days_supply'])),
          review_period_days=a['review_period_days'],lost_sale_penalty=r.last_price*a['lost_sale_penalty_to_price'],
          minimum_order_quantity=a['minimum_order_quantity'],case_pack_size=a['case_pack_size'],
          assumption_type='simulated_not_walmart',seed=cfg['seed']))
    return pd.DataFrame(rows)
