"""Deterministic synthetic integration inputs; never masquerade as M5/DataCo."""
from pathlib import Path
import numpy as np
import pandas as pd

def create_fixture(root,seed=42):
    root=Path(root);m5=root/'m5';dc=root/'dataco';m5.mkdir(parents=True,exist_ok=True);dc.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(seed);days=600;dates=pd.date_range('2015-01-01',periods=days+120)
    cal=pd.DataFrame({'date':dates,'wm_yr_wk':np.arange(len(dates))//7+1000,'d':['d_'+str(i+1) for i in range(len(dates))]})
    for state in ['CA','TX','WI']: cal['snap_'+state]=(dates.day<=10).astype(int)
    event=np.arange(len(dates))%60==0
    cal['event_name_1']=np.where(event,'Synthetic Festival',None);cal['event_type_1']=np.where(event,'Cultural',None)
    cal['event_name_2']=None;cal['event_type_2']=None;cal.to_csv(m5/'calendar.csv',index=False)
    sales=[];prices=[]
    for store,state in [('CA_1','CA'),('TX_1','TX'),('WI_1','WI')]:
        for item in range(1,13):
            iid=f'SYNTH_{item:03d}';price=2+item*.7
            mean=(item%5+1)*(1+.35*(dates[:days].dayofweek>=5))*(1+.5*event[:days])
            demand=rng.poisson(mean);demand=demand*(rng.random(days)>.55) if item%5==0 else demand
            row=dict(id=iid+'_'+store+'_evaluation',item_id=iid,dept_id='D'+str(item%3),cat_id='C'+str((item%3)%2),store_id=store,state_id=state)
            row.update({'d_'+str(j+1):int(v) for j,v in enumerate(demand)});sales.append(row)
            prices.extend(dict(store_id=store,item_id=iid,wm_yr_wk=int(w),sell_price=price) for w in cal.wm_yr_wk.unique())
    pd.DataFrame(sales).to_csv(m5/'sales_train_evaluation.csv',index=False);pd.DataFrame(prices).to_csv(m5/'sell_prices.csv',index=False)
    orders=[];line=0
    for order in range(1,241):
        date=pd.Timestamp('2016-01-01')+pd.Timedelta(days=order//2);scheduled=int(rng.choice([2,4]));actual=max(1,scheduled+int(rng.choice([-1,0,0,1,2,3])))
        for j in range(int(rng.integers(1,4))):
            line+=1;sales=float(rng.uniform(20,200));profit=sales*float(rng.uniform(-.2,.3))
            orders.append({'Order Id':order,'Order Item Id':line,'order date (DateOrders)':date,'shipping date (DateOrders)':date+pd.Timedelta(days=actual),
             'Days for shipping (real)':actual,'Days for shipment (scheduled)':scheduled,'Late_delivery_risk':int(actual>scheduled),
             'Shipping Mode':'Standard Class' if scheduled==4 else 'Second Class','Market':'Europe' if order%2 else 'USCA',
             'Order Region':'West' if order%2 else 'East','Category Name':'Synthetic Category '+str(j%2),'Customer Segment':'Consumer',
             'Product Name':'Synthetic Product '+str(j),'Order Item Quantity':2,'Order Item Total':sales,'Sales':sales,
             'Benefit per order':profit,'Order Profit Per Order':profit,'Order Item Profit Ratio':profit/sales,'Order Status':'Complete',
             'Customer Fname':'PRIVATE_TEST_NAME','Customer Email':'private@example.invalid','Customer Password':'DO_NOT_EXPORT'})
    pd.DataFrame(orders).to_csv(dc/'DataCoSupplyChainDataset.csv',index=False,encoding='utf-8')
    (root/'SYNTHETIC_FIXTURE.txt').write_text('Generated synthetic integration data. No real retailer observations.\n')
    return m5,dc
