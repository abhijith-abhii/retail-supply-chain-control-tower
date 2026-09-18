def required_columns(columns, required, label):
    missing=set(required)-set(columns)
    if missing: raise ValueError(f"{label}: missing required columns {sorted(missing)}")
def unique_keys(frame, keys):
    if frame[keys].isna().any().any() or frame.duplicated(keys).any():
        raise ValueError(f"Null or duplicate key: {keys}")
def require_zero(con, query, message):
    if con.execute(query).fetchone()[0]: raise ValueError(message)
