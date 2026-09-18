from pathlib import Path
from src.utils.file_utils import sql_literal

def detect_sales(raw):
    for name in ("sales_train_evaluation.csv", "sales_train_validation.csv"):
        if (Path(raw)/name).exists(): return Path(raw)/name
    raise FileNotFoundError(f"No M5 sales_train_evaluation.csv or sales_train_validation.csv in {raw}")
def load_m5(con, raw):
    raw=Path(raw); sales=detect_sales(raw)
    for name,path in {"raw_sales":sales,"calendar":raw/"calendar.csv","prices":raw/"sell_prices.csv"}.items():
        if not path.exists(): raise FileNotFoundError(path)
        con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_csv_auto({sql_literal(path)}, sample_size=-1)")
    return sales
