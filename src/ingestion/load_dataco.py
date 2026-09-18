from pathlib import Path
from charset_normalizer import from_bytes
import pandas as pd
from src.utils.file_utils import snake_case, write_json
# Explicit allowlist: unrecognized fields, customer IDs and PII never leave ingestion.
ALLOWED = {"order_id","order_item_id","order_date_dateorders","shipping_date_dateorders",
 "days_for_shipping_real","days_for_shipment_scheduled","late_delivery_risk","delivery_status",
 "shipping_mode","market","order_region","category_name","customer_segment","product_name",
 "order_item_product_price","order_item_quantity","order_item_total","sales","benefit_per_order",
 "order_profit_per_order","order_item_profit_ratio","order_status","product_card_id"}

def load_dataco(path, cfg, report_dir):
    path=Path(path)
    if not path.exists(): raise FileNotFoundError(path)
    sample=path.open("rb").read(1_000_000)
    try: sample.decode("utf-8"); encoding="utf-8"
    except UnicodeDecodeError:
        best=from_bytes(sample).best()
        if best is None: raise ValueError("Encoding detection failed; transcode the source explicitly")
        encoding=best.encoding
    chunks=[]; removed=set(); mappings=cfg.get("aliases",{})
    for x in pd.read_csv(path,encoding=encoding,chunksize=50000):
        x.columns=[mappings.get(snake_case(c),snake_case(c)) for c in x.columns]
        if x.columns.duplicated().any(): raise ValueError("Column normalization collision")
        removed.update(set(x.columns)-ALLOWED)
        x=x[[c for c in x if c in ALLOWED]].copy()
        for c in x.select_dtypes(include="object"):
            x[c]=x[c].str.strip()
        chunks.append(x)
    frame=pd.concat(chunks,ignore_index=True)
    write_json(Path(report_dir)/"dataco_ingestion.json", {"encoding":encoding,"dropped_column_names":sorted(removed),
      "note":"Customer identifiers and all non-allowlisted fields dropped before analytical storage."})
    return frame,encoding
