import pytest
from core import load,analyze

def test_privacy_allowlist():
 df=load();assert not any('Email' in c or 'Password' in c or 'Fname' in c for c in df.columns)
def test_profit_reconciliation():
 d=analyze({});assert sum(r['profit_usd'] for r in d['rows'])==pytest.approx(d['details']['profit_usd'],abs=.02)
 assert sum(r['revenue_usd'] for r in d['rows'])==pytest.approx(d['details']['revenue_usd'],abs=.02)
def test_filter_reduces_cohort():
 assert analyze({'market':'Europe'})['details']['selected_lines']<analyze({})['details']['selected_lines']
def test_unknown_filter():
 with pytest.raises(ValueError):analyze({'market':'invented'})
