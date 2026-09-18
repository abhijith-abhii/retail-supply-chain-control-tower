import json
import re
from pathlib import Path
import pandas as pd

def snake_case(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")
def sql_literal(value):
    return "'" + str(value).replace("'", "''") + "'"
def quote_identifier(value):
    return '"' + str(value).replace('"', '""') + '"'
def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, default=str, allow_nan=False))
def export_frame(df, name, out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    df.to_parquet(out / (name+".parquet"), index=False)
    df.to_csv(out / (name+".csv"), index=False)
    return df
