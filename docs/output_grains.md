# Output grains and aggregation rules

| Output family | Grain | Aggregation rule |
|---|---|---|
| sales_daily | item_id, store_id, date | Units/revenue sum; price must be weighted |
| sales_monthly / weekly / trend | period | Sum quantities and revenue within the same source |
| m5_by_* | named dimension | Raw totals and item-store-day averages; do not add averages |
| product_store_performance / abc_xyz_segmentation | item_id, store_id | Trailing 90 days at latest date; classes are cohort-relative |
| demand_forecasts_28d | item_id, store_id, origin, date, model | One selected model/current origin; intervals cannot be summed as aggregate bounds |
| forecast_backtest_all | item_id, store_id, origin, date, model | Filter to a model and fold; do not sum repeated actuals across candidates |
| forecast_backtest_selected | item_id, store_id, date | Locked final-test observations for selected model |
| forecast_model_metrics | model, fold, forecast_level | Do not average WAPE; use matched errors/actuals to recompute |
| forecast_accuracy_by_segment | segment_type, segment, model | Final-test ratios; segment labels frozen at test origin |
| inventory_assumptions | item_id, store_id | Simulated per-pair inputs; never aggregate rates or service targets |
| inventory_policy_recommendations / stockout_risk / excess_inventory | item_id, store_id, as_of_date, target_service_level | Choose one service and snapshot before adding units/value |
| inventory_simulation_daily | item_id, store_id, date, policy, scenario, run_id, target_service_level | Sum within a world, average across run_id |
| inventory_simulation_kpis | item_id, store_id, policy, scenario, run_id, target_service_level | Portfolio fill=total fulfilled/total demand; average stock over dates, not sum over time |
| inventory_sensitivity | same KPI grain with scenario-specific factor and multiplier | Compare paired baseline/optimized within same scenario/service/run |
| dataco_delivery_performance | order_id | Distinct eligible orders are denominator, not lines |
| dataco_profitability | order_item_id | Add configured line amounts; order profit sums matching lines |
| dataco_order_profit | order_id | Complete valid-line order totals; distinct orders |
| dataco_shipping_mode_performance | dimension, segment | Includes mode, market, region and segment; choose one dimension family |
| dataco_category_delivery | category | Distinct order-category counts; not additive across categories |
| dataco_profitability_summary | dimension, segment | Choose one family; recompute margins from sums |
| executive_kpis | domain, metric | Heterogeneous units, never one combined total |
| recommendations | one evidence-backed suggested action | Text evidence points to explicit source table and provenance |
| dim_* | named natural key (date_key for calendar) | One-side key uniqueness required |
| bridge_date_event | date_key, event_name | Many events per date; avoid joining directly into revenue aggregation |
| fact_sell_price | item_id, store_id, wm_yr_wk | One weekly listed price |
| refresh_metadata | one row per exported run | Refresh timestamp and provenance |

Missing metrics remain null; missing optional source fields are documented in dataco_quality.json. Dates, currency domains, forecast origins and scenario IDs must remain visible to reviewers. Generated dictionaries list all actual exported fields; optional risk outputs add model-level classifier metrics and model-feature importance values.
