# Executive evidence report

Data provenance: **SYNTHETIC FIXTURE — engineering validation only**. Forecasts are estimates; inventory economics are simulated scenario estimates.
No savings represent measured operational changes. M5 and DataCo are independent domains.

## Forecast evidence
Selected model: `lightgbm` using the pre-test selection fold. Held-out WAPE: 45.52%; MAE: 1.406; normalized bias: -0.05%.
Empirical held-out interval coverage: 80% band 74.14%; 95% band 89.88%.
Source: `forecast_model_metrics`, `forecast_backtest_selected`.

## Inventory scenario evidence
At 95% target service, optimized average total cost across runs: 195.94 currency units.
Baseline minus optimized cost: 1,148.25 currency units (negative means optimized costs more).
Source: `inventory_simulation_kpis`; preserve service level and average across runs before aggregation.
Highest modeled starting-stock risk: SYNTH_005/WI_1, probability 39.09%.
Source: `stockout_risk`; assumes no initial purchase orders and simulated opening inventory.
Recommendation: verify lead times and opening stock for this pair before applying its replenishment recommendation.

## Logistics evidence
Shipping mode with largest observed late share: second class, 64/129 eligible orders (49.61%).
Source: `dataco_shipping_mode_performance`. Investigate capacity and promise-setting; association does not establish cause.

## Decision gates
Pilot inventory changes only after validating real procurement costs, inventory positions and supplier distributions.
Evaluate profit and service trade-offs across `inventory_sensitivity`; do not select a policy solely for lower stockouts.
Review sparse segments and uncertainty before stocking for event-associated uplift. SNAP is benefit eligibility, not a promotion flag.
If this report uses fixtures, every observation above describes the synthetic fixture only and is not a business finding.
