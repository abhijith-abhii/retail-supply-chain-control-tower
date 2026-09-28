from pathlib import Path
import pandas as pd,numpy as np
ROOT=Path(__file__).parent
# Explicit allowlist excludes the original fixture's deliberate privacy-test canaries.
COLS=['Order Id','Order Item Id','order date (DateOrders)','Days for shipping (real)','Days for shipment (scheduled)','Shipping Mode','Market','Order Region','Category Name','Customer Segment','Product Name','Order Item Quantity','Order Item Total','Benefit per order','Order Status']
def load():
 df=pd.read_csv(ROOT/'data/sample/dataco/DataCoSupplyChainDataset.csv',usecols=COLS)
 if df['Order Item Id'].duplicated().any():raise ValueError('Duplicate line item IDs')
 df['date']=pd.to_datetime(df['order date (DateOrders)'],errors='raise');df['month']=df.date.dt.strftime('%Y-%m')
 for col in ['Order Item Total','Benefit per order','Days for shipping (real)','Days for shipment (scheduled)']:
  df[col]=pd.to_numeric(df[col],errors='raise')
  if not np.isfinite(df[col]).all():raise ValueError('Missing or nonfinite '+col)
 return df

def analyze(p):
 df=load();market=p.get('market','all');segment=p.get('segment','all');month=p.get('month','all')
 for value,column in [(market,'Market'),(segment,'Customer Segment'),(month,'month')]:
  if value!='all' and value not in df[column].unique():raise ValueError('Unsupported '+column+' filter')
 selected=df.copy()
 for value,column in [(market,'Market'),(segment,'Customer Segment'),(month,'month')]:
  if value!='all':selected=selected[selected[column]==value]
 # Shipping is order-level. Reject inconsistent line-level shipping values before aggregating.
 consistency=selected.groupby('Order Id')[['Days for shipping (real)','Days for shipment (scheduled)']].nunique()
 if (consistency>1).any().any():raise ValueError('Inconsistent shipping values within an order')
 orders=selected.drop_duplicates('Order Id');late=orders['Days for shipping (real)']>orders['Days for shipment (scheduled)'];revenue=float(selected['Order Item Total'].sum());profit=float(selected['Benefit per order'].sum())
 g=selected.groupby('Category Name').agg(revenue_usd=('Order Item Total','sum'),profit_usd=('Benefit per order','sum'),units=('Order Item Quantity','sum'),lines=('Order Item Id','count')).reset_index();g['margin_pct']=100*g.profit_usd/g.revenue_usd.replace(0,np.nan);g=g.round(2).replace({np.nan:None})
 trend=selected.groupby('month')['Order Item Total'].sum()
 return dict(metrics={'Orders':len(orders),'Revenue':f'${revenue:,.2f}','Profit':f'${profit:,.2f}','Late order share':f'{late.mean():.1%}' if len(orders) else 'No orders'},rows=g.to_dict('records'),bars=[dict(label=k,value=round(float(v),2)) for k,v in trend.items()],chart_title='Selected revenue by month',details={'filters':p,'source_rows':len(df),'selected_lines':len(selected),'revenue_usd':revenue,'profit_usd':profit,'late_orders':int(late.sum()),'order_count':len(orders),'definitions':{'revenue':'sum of source line totals','profit':'sum of source line benefit','late':'actual shipping days > scheduled days; distinct orders'},'privacy':'Explicit ingestion column allowlist; names, emails and password test columns excluded'},notice='Synthetic operational analysis. Profit excludes costs absent from the source. Filtering to a category or segment changes the observed cohort; these are descriptive comparisons.')
