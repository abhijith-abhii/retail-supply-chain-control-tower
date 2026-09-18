import pandas as pd
import numpy as np
from src.validation.schema_validation import required_columns,unique_keys
from src.utils.file_utils import write_json
from pathlib import Path

def transform_dataco(x,cfg,reports):
    x=x.copy();required=['order_id','order_item_id','order_date_dateorders']
    required_columns(x.columns,required,'DataCo')
    unique_keys(x,['order_item_id'])
    issues={'source_rows':len(x),'repeated_order_ids_expected_for_lines':int(x.order_id.duplicated().sum()),'missing_optional_columns':[]}
    for c in ['shipping_mode','market','order_region','category_name','customer_segment','product_name','order_status']:
        if c not in x: x[c]='Unknown';issues['missing_optional_columns'].append(c)
        x[c]=x[c].fillna('Unknown').astype(str).str.strip().str.casefold().replace(cfg.get('category_mappings',{}))
    for raw,clean in [('order_date_dateorders','order_date'),('shipping_date_dateorders','shipping_date')]:
        if raw in x:
            x[clean]=pd.to_datetime(x[raw],format='mixed',errors='coerce').dt.normalize()
            issues[clean+'_invalid']=int(x[clean].isna().sum())
        else: x[clean]=pd.NaT;issues['missing_optional_columns'].append(raw)
    if x.order_date.isna().any(): raise ValueError('Invalid DataCo order dates; see source audit')
    x['date_key']=x.order_date.dt.strftime('%Y%m%d').astype(int)
    for raw,clean in [('days_for_shipping_real','actual_shipping_days'),('days_for_shipment_scheduled','scheduled_shipping_days'),
                       ('order_item_quantity','quantity'),(cfg['net_sales_source'],'sales'),(cfg['profit_source'],'profit')]:
        if raw not in x: x[clean]=np.nan;issues['missing_optional_columns'].append(raw)
        else: x[clean]=pd.to_numeric(x[raw],errors='coerce')
    x['invalid_sales_flag']=x.sales.lt(0)|x.quantity.lt(0)
    x['abnormal_profit_flag']=x.profit.abs()>x.sales.abs()*2
    x['delivery_eligible']=x.actual_shipping_days.between(0,cfg['maximum_shipping_days']) & x.scheduled_shipping_days.between(0,cfg['maximum_shipping_days']) & ~x.order_status.isin(['canceled','cancelled','suspected_fraud','suspected fraud'])
    x['delay_days']=(x.actual_shipping_days-x.scheduled_shipping_days).where(x.delivery_eligible)
    x['late_order']=x.delay_days.gt(0).astype('Int64').where(x.delivery_eligible)
    x['positive_delay_days']=x.delay_days.clip(lower=0)
    x['date_duration_mismatch']=((x.shipping_date-x.order_date).dt.days-x.actual_shipping_days).abs().gt(1) & x.shipping_date.notna()
    if 'late_delivery_risk' in x:
        issues['source_late_flag_disagreement']=int((pd.to_numeric(x.late_delivery_risk,errors='coerce').ne(x.late_order)&x.delivery_eligible).sum())
    issues.update(invalid_sales_rows=int(x.invalid_sales_flag.sum()),abnormal_profit_rows=int(x.abnormal_profit_flag.sum()),ineligible_delivery_rows=int((~x.delivery_eligible).sum()),date_duration_mismatch=int(x.date_duration_mismatch.sum()))
    write_json(Path(reports)/'dataco_quality.json',issues)
    # Group dimensions describing an order must agree; never silently choose an arbitrary category/mode.
    cols=['order_date','shipping_mode','market','order_region','customer_segment','actual_shipping_days','scheduled_shipping_days','delivery_eligible','late_order','delay_days','positive_delay_days']
    conflicts=x.groupby('order_id')[cols].nunique(dropna=False).gt(1).any(axis=1)
    if conflicts.any(): raise ValueError(f'{int(conflicts.sum())} DataCo orders have conflicting shipment attributes; define shipment-level keys before proceeding')
    delivery=x.groupby('order_id',as_index=False)[cols+['date_key']].first()
    delivery=delivery.rename(columns={'order_region':'region'})
    linecols=['order_item_id','order_id','order_date','date_key','shipping_mode','market','order_region','category_name','customer_segment','product_name','quantity','sales','profit','invalid_sales_flag','abnormal_profit_flag']
    lines=x[linecols].rename(columns={'order_region':'region','category_name':'category'})
    lines['profit_margin']=lines.profit.div(lines.sales.replace(0,np.nan))
    lines['loss_making_line']=lines.profit.lt(0)
    return lines,delivery
