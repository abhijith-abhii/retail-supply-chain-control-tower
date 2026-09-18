from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]
def load_config(path=None):
    cfg = yaml.safe_load(Path(path or ROOT / "config/project_config.yaml").read_text())
    assert cfg["forecast_horizon"] == 28, "Production demand horizon must be 28 days"
    assert cfg["backtest_folds"] >= 3
    assert cfg["inventory"]["simulation_days"] in (28, 90)
    assert all(0 < s < 1 for s in cfg["inventory"]["service_levels"])
    return cfg
