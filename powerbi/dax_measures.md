# DAX measure catalogue
Create these measures in `_Measures`. Import exact table names from data_model.md. Every DIVIDE intentionally returns BLANK for unavailable denominators. Measures are specified for Power BI Desktop; no Desktop engine was available for native DAX validation.

## Total Units Sold
```dax
Total Units Sold =
SUM(sales_daily[units_sold])
```
Definition: Recorded M5 sales units.

Required fields: sales_daily[units_sold]. Format: `#,0`.

Filter context: Respects the active dimensions and page filters.

## Total Revenue
```dax
Total Revenue =
SUM(sales_daily[revenue])
```
Definition: M5 units multiplied by weekly price.

Required fields: sales_daily[revenue]. Format: `#,0.00`.

Filter context: Respects the active dimensions and page filters.

## Average Selling Price
```dax
Average Selling Price =
DIVIDE([Total Revenue], [Total Units Sold])
```
Definition: Weighted unit selling price.

Required fields: Revenue and units measures. Format: `#,0.00`.

Filter context: Respects the active dimensions and page filters.

## Revenue Previous Period
```dax
Revenue Previous Period =
CALCULATE([Total Revenue], DATEADD(dim_date[date], -1, MONTH))
```
Definition: Revenue for the same date selection shifted one month.

Required fields: dim_date[date]. Format: `#,0.00`.

Filter context: Use a contiguous date selection; compare like-for-like partial periods.

## Revenue Growth %
```dax
Revenue Growth % =
DIVIDE([Total Revenue] - [Revenue Previous Period], [Revenue Previous Period])
```
Definition: Relative revenue change.

Required fields: Revenue measures. Format: `0.0%`.

Filter context: Respects the active dimensions and page filters.

## Forecast Units
```dax
Forecast Units =
SUM(demand_forecasts_28d[forecast_units])
```
Definition: Next-28-day selected-model demand.

Required fields: demand_forecasts_28d[forecast_units]. Format: `#,0.0`.

Filter context: Use forecast dates; historical date filters can legitimately return blank.

## Actual Units
```dax
Actual Units =
SUM(forecast_backtest_selected[actual_units])
```
Definition: Actual units on the locked evaluation observations.

Required fields: forecast_backtest_selected[actual_units]. Format: `#,0`.

Filter context: Respects the active dimensions and page filters.

## Forecast Error
```dax
Forecast Error =
SUM(forecast_backtest_selected[error])
```
Definition: Prediction minus actual on matched test dates.

Required fields: forecast_backtest_selected[error]. Format: `#,0.0`.

Filter context: Respects the active dimensions and page filters.

## Absolute Forecast Error
```dax
Absolute Forecast Error =
SUM(forecast_backtest_selected[absolute_error])
```
Definition: Sum of row absolute error, not absolute sum of errors.

Required fields: forecast_backtest_selected[absolute_error]. Format: `#,0.0`.

Filter context: Respects the active dimensions and page filters.

## Forecast WAPE
```dax
Forecast WAPE =
DIVIDE([Absolute Forecast Error], [Actual Units])
```
Definition: Demand-weighted absolute error.

Required fields: Matched actual/error measures. Format: `0.0%`.

Filter context: Never average exported row WAPEs; denominator zero returns blank.

## Forecast Bias
```dax
Forecast Bias =
DIVIDE([Forecast Error], [Actual Units])
```
Definition: Normalized forecast bias; positive means overforecast.

Required fields: Matched actual/error measures. Format: `0.0%`.

Filter context: Respects the active dimensions and page filters.

## Scenario Ready
```dax
Scenario Ready =
IF(HASONEVALUE(ServiceLevel[value]) && HASONEVALUE(Policy[name]) && HASONEVALUE(Scenario[name]), 1, 0)
```
Definition: Guard against adding incompatible scenario worlds.

Required fields: ServiceLevel, Policy, Scenario. Format: `0`.

Filter context: Set single-select slicers and default 0.95 / optimized / base.

## Inventory Value
```dax
Inventory Value =
IF(HASONEVALUE(ServiceLevel[value]), SUM(inventory_policy_recommendations[inventory_value]))
```
Definition: Assumed initial inventory investment.

Required fields: inventory_policy_recommendations[inventory_value]. Format: `#,0.0`.

Filter context: One service level and one exported as-of snapshot; historical date slicers do not filter this table.

## Safety Stock Units
```dax
Safety Stock Units =
IF(HASONEVALUE(ServiceLevel[value]), SUM(inventory_policy_recommendations[safety_stock]))
```
Definition: Lead-time safety units under independence and normal approximation.

Required fields: inventory_policy_recommendations[safety_stock]. Format: `#,0.0`.

Filter context: One service level and one exported as-of snapshot; historical date slicers do not filter this table.

## Reorder Point Units
```dax
Reorder Point Units =
IF(HASONEVALUE(ServiceLevel[value]), SUM(inventory_policy_recommendations[reorder_point]))
```
Definition: Expected lead-time demand plus safety stock.

Required fields: inventory_policy_recommendations[reorder_point]. Format: `#,0.0`.

Filter context: One service level and one exported as-of snapshot; historical date slicers do not filter this table.

## EOQ Units
```dax
EOQ Units =
IF(HASONEVALUE(ServiceLevel[value]), SUM(inventory_policy_recommendations[eoq]))
```
Definition: Classical economic lot-size recommendation.

Required fields: inventory_policy_recommendations[eoq]. Format: `#,0.0`.

Filter context: One service level and one exported as-of snapshot; historical date slicers do not filter this table.

## Estimated Excess Inventory
```dax
Estimated Excess Inventory =
IF(HASONEVALUE(ServiceLevel[value]), SUM(inventory_policy_recommendations[excess_value]))
```
Definition: Value above forecast protection stock target.

Required fields: inventory_policy_recommendations[excess_value]. Format: `#,0.0`.

Filter context: One service level and one exported as-of snapshot; historical date slicers do not filter this table.

## Days of Supply
```dax
Days of Supply =
IF(HASONEVALUE(ServiceLevel[value]), DIVIDE(SUM(inventory_policy_recommendations[initial_inventory]), SUM(inventory_policy_recommendations[forecast_daily_demand])))
```
Definition: Portfolio starting inventory divided by daily forecast; not sum of item ratios.

Required fields: initial_inventory, forecast_daily_demand. Format: `0.0`.

Filter context: Respects the active dimensions and page filters.

## Products at Stockout Risk
```dax
Products at Stockout Risk =
IF(HASONEVALUE(ServiceLevel[value]), COUNTROWS(FILTER(inventory_policy_recommendations, inventory_policy_recommendations[stockout_probability] > 1 - inventory_policy_recommendations[target_service_level])))
```
Definition: At-risk item-store pairs, not distinct products.

Required fields: stockout_probability, target_service_level. Format: `#,0`.

Filter context: Respects the active dimensions and page filters.

## Stockout Events
```dax
Stockout Events =
IF([Scenario Ready] = 1, AVERAGEX(VALUES(inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[stockout_event]))))
```
Definition: Mean item-store stockout days across runs.

Required fields: inventory_simulation_daily[stockout_event], [run_id]. Format: `#,0.0`.

Filter context: Preserves selected policy, service and scenario; averages repetitions rather than summing them.

## Lost Sales Units
```dax
Lost Sales Units =
IF([Scenario Ready] = 1, AVERAGEX(VALUES(inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[lost_sales_units]))))
```
Definition: Mean simulated lost units across runs.

Required fields: inventory_simulation_daily[lost_sales_units], [run_id]. Format: `#,0.0`.

Filter context: Preserves selected policy, service and scenario; averages repetitions rather than summing them.

## Lost Sales Value
```dax
Lost Sales Value =
IF([Scenario Ready] = 1, AVERAGEX(VALUES(inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[lost_sales_value]))))
```
Definition: Mean simulated lost units at assumed selling price.

Required fields: inventory_simulation_daily[lost_sales_value], [run_id]. Format: `#,0.00`.

Filter context: Preserves selected policy, service and scenario; averages repetitions rather than summing them.

## Total Holding Cost
```dax
Total Holding Cost =
IF([Scenario Ready] = 1, AVERAGEX(VALUES(inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[holding_cost]))))
```
Definition: Mean end-of-day stock holding cost.

Required fields: inventory_simulation_daily[holding_cost], [run_id]. Format: `#,0.00`.

Filter context: Preserves selected policy, service and scenario; averages repetitions rather than summing them.

## Total Ordering Cost
```dax
Total Ordering Cost =
IF([Scenario Ready] = 1, AVERAGEX(VALUES(inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[ordering_cost]))))
```
Definition: Mean placed-order fixed cost.

Required fields: inventory_simulation_daily[ordering_cost], [run_id]. Format: `#,0.00`.

Filter context: Preserves selected policy, service and scenario; averages repetitions rather than summing them.

## Total Inventory Cost
```dax
Total Inventory Cost =
IF([Scenario Ready] = 1, AVERAGEX(VALUES(inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[total_inventory_cost]))))
```
Definition: Mean holding plus ordering plus lost-sale penalty; excludes purchase cash flow.

Required fields: inventory_simulation_daily[total_inventory_cost], [run_id]. Format: `#,0.00`.

Filter context: Preserves selected policy, service and scenario; averages repetitions rather than summing them.

## Stockout Rate
```dax
Stockout Rate =
IF([Scenario Ready] = 1, DIVIDE(SUM(inventory_simulation_daily[stockout_event]), COUNTROWS(inventory_simulation_daily)))
```
Definition: Share of simulated item-store-days with lost demand.

Required fields: stockout_event. Format: `0.0%`.

Filter context: Respects the active dimensions and page filters.

## Fill Rate
```dax
Fill Rate =
IF([Scenario Ready] = 1, DIVIDE(SUM(inventory_simulation_daily[fulfilled_units]), SUM(inventory_simulation_daily[actual_demand])))
```
Definition: Demand-weighted fraction fulfilled.

Required fields: fulfilled_units, actual_demand. Format: `0.0%`.

Filter context: Respects the active dimensions and page filters.

## Average Inventory
```dax
Average Inventory =
IF([Scenario Ready] = 1, AVERAGEX(SUMMARIZE(inventory_simulation_daily, inventory_simulation_daily[date], inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[closing_inventory]))))
```
Definition: Average portfolio units over dates and runs.

Required fields: date, run_id, closing_inventory. Format: `#,0.0`.

Filter context: Requires the complete same date grid per selected item-store.

## Inventory Turnover
```dax
Inventory Turnover =
VAR Fulfilled = AVERAGEX(VALUES(inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[fulfilled_units]))) VAR Days = DISTINCTCOUNT(inventory_simulation_daily[date]) RETURN IF([Scenario Ready] = 1, DIVIDE(Fulfilled, [Average Inventory]) * DIVIDE(365, Days))
```
Definition: Annualized unit turnover for the selected horizon.

Required fields: fulfilled_units, run_id, date, Average Inventory. Format: `0.0x`.

Filter context: Unit proxy; for true financial turnover use actual COGS and average inventory cost.

## Baseline Inventory Cost
```dax
Baseline Inventory Cost =
CALCULATE([Total Inventory Cost], REMOVEFILTERS(Policy), Policy[name] = "baseline")
```
Definition: Baseline cost on matching service and scenario.

Required fields: Total Inventory Cost, Policy. Format: `#,0.00`.

Filter context: Respects the active dimensions and page filters.

## Optimized Inventory Cost
```dax
Optimized Inventory Cost =
CALCULATE([Total Inventory Cost], REMOVEFILTERS(Policy), Policy[name] = "optimized")
```
Definition: Forecast-driven cost on matching service and scenario.

Required fields: Total Inventory Cost, Policy. Format: `#,0.00`.

Filter context: Respects the active dimensions and page filters.

## Estimated Cost Reduction
```dax
Estimated Cost Reduction =
[Baseline Inventory Cost] - [Optimized Inventory Cost]
```
Definition: Scenario cost reduction; negative is a deterioration.

Required fields: Baseline and optimized measures. Format: `#,0.00`.

Filter context: Respects the active dimensions and page filters.

## Estimated Cost Reduction %
```dax
Estimated Cost Reduction % =
DIVIDE([Estimated Cost Reduction], [Baseline Inventory Cost])
```
Definition: Relative scenario cost reduction.

Required fields: Scenario cost measures. Format: `0.0%`.

Filter context: Respects the active dimensions and page filters.

## Total Orders
```dax
Total Orders =
DISTINCTCOUNT(dataco_delivery_performance[order_id])
```
Definition: All DataCo business orders in scope.

Required fields: dataco_delivery_performance[order_id]. Format: `#,0`.

Filter context: Category filters do not reach this order fact; use Category Late Delivery % for category analysis.

## Eligible Orders
```dax
Eligible Orders =
CALCULATE([Total Orders], dataco_delivery_performance[delivery_eligible] = TRUE())
```
Definition: Orders with valid shipment durations and eligible status.

Required fields: delivery_eligible. Format: `#,0`.

Filter context: Respects the active dimensions and page filters.

## Late Orders
```dax
Late Orders =
CALCULATE([Total Orders], dataco_delivery_performance[delivery_eligible] = TRUE(), dataco_delivery_performance[late_order] = 1)
```
Definition: Eligible orders exceeding scheduled shipping duration.

Required fields: delivery_eligible, late_order. Format: `#,0`.

Filter context: Respects the active dimensions and page filters.

## Late Delivery %
```dax
Late Delivery % =
DIVIDE([Late Orders], [Eligible Orders])
```
Definition: Late share of eligible orders.

Required fields: Late Orders, Eligible Orders. Format: `0.0%`.

Filter context: Respects the active dimensions and page filters.

## On-Time Delivery %
```dax
On-Time Delivery % =
IF([Eligible Orders] > 0, 1 - [Late Delivery %])
```
Definition: On-time share on the same eligibility denominator.

Required fields: Eligible Orders, Late Delivery %. Format: `0.0%`.

Filter context: Respects the active dimensions and page filters.

## Average Delay Days
```dax
Average Delay Days =
CALCULATE(AVERAGE(dataco_delivery_performance[positive_delay_days]), dataco_delivery_performance[delivery_eligible] = TRUE())
```
Definition: Positive delay averaged across all eligible orders, including zero delays.

Required fields: positive_delay_days, delivery_eligible. Format: `0.0`.

Filter context: Respects the active dimensions and page filters.

## Total Sales
```dax
Total Sales =
CALCULATE(SUM(dataco_profitability[sales]), dataco_profitability[invalid_sales_flag] = FALSE())
```
Definition: DataCo configured line net sales, excluding invalid sales/quantity rows.

Required fields: dataco_profitability[sales], invalid_sales_flag. Format: `#,0.00`.

Filter context: Respects the active dimensions and page filters.

## Total Profit
```dax
Total Profit =
CALCULATE(SUM(dataco_profitability[profit]), dataco_profitability[invalid_sales_flag] = FALSE())
```
Definition: DataCo configured line profit. Abnormal profit rows remain flagged for review.

Required fields: dataco_profitability[profit], invalid_sales_flag. Format: `#,0.00`.

Filter context: Respects the active dimensions and page filters.

## Profit Margin %
```dax
Profit Margin % =
DIVIDE([Total Profit], [Total Sales])
```
Definition: Ratio of aggregate profit to aggregate net sales.

Required fields: Total Profit, Total Sales. Format: `0.0%`.

Filter context: Respects the active dimensions and page filters.

## Loss-Making Orders
```dax
Loss-Making Orders =
COUNTROWS(FILTER(VALUES(dataco_profitability[order_id]), CALCULATE([Total Profit]) < 0))
```
Definition: Orders whose line profit sums to a loss within the current scope.

Required fields: dataco_profitability[order_id], Total Profit. Format: `#,0`.

Filter context: With category filters this is an order-category scoped loss, not the full-order economic outcome. Use no category filter for full-order loss.

## Category Late Delivery %
```dax
Category Late Delivery % =
VAR OrdersInCategory = VALUES(dataco_profitability[order_id]) RETURN CALCULATE([Late Delivery %], TREATAS(OrdersInCategory, dataco_delivery_performance[order_id]))
```
Definition: Late share of distinct orders containing selected categories.

Required fields: order_id in both DataCo facts. Format: `0.0%`.

Filter context: Explicit virtual relationship only; multi-category order counts cannot be added across category rows.

## Last Refresh Date
```dax
Last Refresh Date =
MAX(refresh_metadata[last_refresh_utc])
```
Definition: UTC timestamp written after pipeline exports.

Required fields: refresh_metadata[last_refresh_utc]. Format: `Text`.

Filter context: Unaffected by slicers; do not use NOW(), which reports viewing time.

## Dynamic Demand Title
```dax
Dynamic Demand Title =
"Demand forecast | " & COALESCE(SELECTEDVALUE(dim_store[store_id]), "Selected stores") & " | 28 days"
```
Definition: Selection-aware title.

Required fields: dim_store[store_id]. Format: `Text`.

Filter context: Respects the active dimensions and page filters.
