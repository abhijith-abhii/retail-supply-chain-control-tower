# Relationship specification

Import one run folder only: `data/powerbi/fixture`, `sample`, or `full`. Never combine fixture and Kaggle runs. Keep names exactly as exported, because DAX uses these names. Create an empty `_Measures` table and hide its placeholder field.

All relationships below are active, 1:* and single direction from dimension to fact unless noted. Disable automatic relationship detection and auto date/time. Mark `dim_date[date]` as date table. `dim_order_date` is an independent role-playing copy for DataCo, permitting different source date ranges. Do not relate the two date tables.

| Dimension key | Fact and foreign key | Grain / constraint |
|---|---|---|
| dim_date[date] | sales_daily[date] | item-store-day |
| dim_date[date] | demand_forecasts_28d[date] | one current origin and selected model |
| dim_date[date] | forecast_backtest_selected[date] | locked test, selected model |
| dim_date[date] | inventory_simulation_daily[date] | item-store-date-policy-service-run-scenario |
| dim_product[item_id] | sales_daily, demand_forecasts_28d, forecast_backtest_selected, inventory_policy_recommendations, inventory_simulation_daily, product_store_performance: [item_id] | M5 only |
| dim_store[store_id] | same six M5 tables: [store_id] | M5 only |
| dim_order_date[date] | dataco_profitability[order_date], dataco_delivery_performance[order_date] | line fact and order fact respectively |
| dim_product_category[category] | dataco_profitability[category] | does not directly filter order fact |
| dim_market[market] | both DataCo facts [market] | one-to-many each |
| dim_region[region] | both DataCo facts [region] | one-to-many each |
| dim_shipping_mode[shipping_mode] | both DataCo facts [shipping_mode] | one-to-many each |
| dim_customer_segment[customer_segment] | both DataCo facts [customer_segment] | one-to-many each |
| ServiceLevel[value] | inventory_policy_recommendations[target_service_level], inventory_simulation_daily[target_service_level] | single-select 0.95 default |
| Policy[name] | inventory_simulation_daily[policy] | single-select optimized default |
| Scenario[name] | inventory_simulation_daily[scenario] | base default |

In Power Query merge category and department labels into `dim_product`, and state into `dim_store`. Their exported natural keys already identify those values. Do not create a second active path by also linking category to the fact. Hide technical keys and duplicate descriptive fact fields.

Create selector tables in DAX:
```dax
ServiceLevel = DATATABLE("value", DOUBLE, {{0.90},{0.95},{0.98}})
Policy = DATATABLE("name", STRING, {{"baseline"},{"optimized"}})
Scenario = DATATABLE("name", STRING, {{"base"}})
```
`inventory_sensitivity` is a separate scenario mart. If imported, create separate slicers and measures for that table rather than mixing its repeated worlds with base simulation rows.

No fact-to-fact relationships. No M5 product, category, store, state, or customer join to DataCo. Geography meanings do not match. No combined money total across domains. For DataCo category delivery drill-through, use the explicit `TREATAS` measure in dax_measures.md or `dataco_category_delivery`; distinct order-category counts are non-additive across categories.

Snapshot policies have `as_of_date`, not a daily inventory history. Keep them disconnected from historical date slicers and label the as-of date. Simulation dates are historical holdout replay dates. Forecast interval bounds belong to item-store predictions and cannot be summed to claim an aggregate confidence interval. Import only `forecast_backtest_selected` for dashboard accuracy; the all-model table is for comparison research. Accuracy metrics for differing forecast levels must not be averaged.

Power Query data types: IDs text except business order IDs integer; date fields Date; flags Boolean or whole number as exported; rates decimal; currency fields decimal; counts whole or decimal forecast units. Do not replace missing metric values with zero. Use refresh_metadata for provenance and timestamp.
