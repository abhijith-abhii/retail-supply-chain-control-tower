from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
from src.utils.file_utils import sql_literal, quote_identifier, write_json, snake_case
from src.validation.schema_validation import required_columns, require_zero

def audit_csv(path, report_dir, encoding="utf-8"):
    """Bounded Pandas chunks plus DuckDB exact distinct/duplicate counts. No raw PII values in report."""
    path=Path(path); stats={}; rows=0; peak=0; decode_errors=0
    con=duckdb.connect(); con.execute("SET memory_limit='1GB'")
    # For non-UTF8 CSV, stream a UTF8 temporary file; deleted when the audit finishes.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        audit_path=path
        if encoding.lower().replace('-','') not in ('utf8','ascii'):
            audit_path=Path(td)/"audit.csv"
            with path.open(encoding=encoding,errors="strict") as source, audit_path.open('w') as dest:
                for line in source: dest.write(line)
        con.execute(f"CREATE TABLE audit AS SELECT * FROM read_csv_auto({sql_literal(audit_path)}, all_varchar=true)")
        columns=[c[0] for c in con.execute("DESCRIBE audit").fetchall()]
        for chunk in pd.read_csv(path,encoding=encoding,chunksize=10000):
            rows+=len(chunk);peak=max(peak,int(chunk.memory_usage(deep=True).sum()))
            for c in chunk:
                s=chunk[c]; a=stats.setdefault(c,{"dtypes":set(),"missing":0,"negative":0,"zero":0,"minimum":None,"maximum":None,"invalid_dates":0,"date_min":None,"date_max":None,"outliers_iqr_sample":None})
                a['dtypes'].add(str(s.dtype)); a['missing']+=int(s.isna().sum())
                decode_errors+=int(s.astype(str).str.contains('\ufffd',regex=False).sum())
                if pd.api.types.is_numeric_dtype(s) and not any(t in snake_case(c) for t in ["customer_id","customer_id","phone","password","email","street","zip"]):
                    a['negative']+=int((s<0).sum());a['zero']+=int((s==0).sum())
                    if s.notna().any():
                        lo=float(s.min());hi=float(s.max())
                        a['minimum']=lo if a['minimum'] is None else min(lo,a['minimum'])
                        a['maximum']=hi if a['maximum'] is None else max(hi,a['maximum'])
                    if a['outliers_iqr_sample'] is None:
                        q1,q3=s.quantile([.25,.75]);iqr=q3-q1
                        a['outliers_iqr_sample']=int(((s<q1-1.5*iqr)|(s>q3+1.5*iqr)).sum())
                # Date columns only; never log values for names/addresses/identifiers.
                if 'date' in snake_case(c) and not pd.api.types.is_numeric_dtype(s):
                    d=pd.to_datetime(s,errors='coerce',format='mixed');a['invalid_dates']+=int((s.notna() & d.isna()).sum())
                    if d.notna().any():
                        lo=str(d.min());hi=str(d.max());a['date_min']=min(a['date_min'] or lo,lo);a['date_max']=max(a['date_max'] or hi,hi)
        for c in columns:
            a=stats[c];a['dtypes']=sorted(a['dtypes'])
            a['unique_values']=con.execute(f"SELECT count(DISTINCT {quote_identifier(c)}) FROM audit").fetchone()[0]
        duplicates=con.execute("SELECT (SELECT count(*) FROM audit)-count(*) FROM (SELECT DISTINCT * FROM audit)").fetchone()[0]
    con.close()
    report={"filename":path.name,"rows":rows,"columns":len(columns),"column_stats":stats,
      "duplicate_rows":duplicates,"encoding":encoding,"replacement_character_count":decode_errors,
      "peak_chunk_memory_bytes":peak,"file_size_bytes":path.stat().st_size,
      "outlier_method":"1.5 IQR on first 10,000 rows per numeric column; descriptive screen, not removal"}
    write_json(Path(report_dir)/(path.stem+"_audit.json"),report)
    return report

def validate_m5(con):
    for table,cols in {"raw_sales":["id","item_id","dept_id","cat_id","store_id","state_id"],
       "calendar":["d","date","wm_yr_wk","snap_CA","snap_TX","snap_WI"],
       "prices":["item_id","store_id","wm_yr_wk","sell_price"]}.items():
        required_columns([x[0] for x in con.execute(f"DESCRIBE {table}").fetchall()],cols,table)
    require_zero(con,"SELECT count(*) FROM (SELECT item_id,store_id FROM raw_sales GROUP BY ALL HAVING count(*)>1)","Duplicate M5 series")
    require_zero(con,"SELECT count(*) FROM (SELECT d FROM calendar GROUP BY d HAVING count(*)>1)","Duplicate calendar day")
    require_zero(con,"SELECT count(*) FROM calendar WHERE try_cast(date AS DATE) IS NULL","Invalid M5 dates")
    require_zero(con,"SELECT count(*) FROM prices WHERE sell_price < 0 OR sell_price IS NULL","Invalid sell prices")
    cols=[c[0] for c in con.execute('DESCRIBE raw_sales').fetchall() if c[0].startswith('d_')]
    if not cols: raise ValueError('No M5 day columns')
    checks=' OR '.join(f'"{c}" IS NULL OR "{c}" < 0' for c in cols)
    require_zero(con,'SELECT count(*) FROM raw_sales WHERE '+checks,'Null or negative raw demand')
    require_zero(con,"SELECT count(*) FROM (SELECT date FROM calendar GROUP BY date HAVING count(*)>1)","Duplicate calendar date")
    require_zero(con,"SELECT count(*) FROM raw_sales WHERE item_id IS NULL OR store_id IS NULL OR state_id NOT IN ('CA','TX','WI')","Invalid M5 identity/state")
    require_zero(con,"SELECT count(*) FROM (SELECT item_id,store_id,wm_yr_wk FROM prices GROUP BY ALL HAVING count(*)>1)","Duplicate weekly price")

def validate_sales(con):
    require_zero(con,"SELECT count(*) FROM sales_long WHERE units_sold IS NULL OR units_sold<0 OR date IS NULL", "Invalid demand/date or missing calendar join")
    require_zero(con,"SELECT count(*) FROM sales_long WHERE units_sold>0 AND sell_price IS NULL", "Positive demand with missing price; correct source before revenue analysis")
    require_zero(con,"SELECT count(*) FROM (SELECT item_id,store_id,date FROM sales_long GROUP BY ALL HAVING count(*)<>1)","Nonunique daily sales")
    require_zero(con,"SELECT count(*) FROM (SELECT item_id,store_id,count(*) n,date_diff('day',min(date),max(date))+1 expected FROM sales_long GROUP BY ALL) WHERE n<>expected","Non-contiguous demand history")
