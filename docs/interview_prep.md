# Interview preparation

## 30-second explanation
I built a retail supply-chain analytics prototype with two separate domains: M5 demand forecasting and simulated replenishment, and DataCo delivery and profitability. It uses DuckDB, Parquet, Python, PostgreSQL and a six-page Power BI specification. The main focus is defensible metrics: time-based forecasting, no customer PII, no invented dataset joins and clearly labeled inventory assumptions.

## 60-second explanation
The pipeline validates raw CSVs, expands M5 sales into a daily product-store panel and produces reusable Parquet and PostgreSQL tables. It compares four baselines with a global LightGBM model using chronological calibration, selection and test windows, then creates a 28-day forecast. I convert that into safety-stock and order policies, replay baseline and optimized replenishment on the same held-out demand, and test assumption sensitivity. DataCo supplies a separate order-level delivery view and line-level profit analysis. The Power BI package specifies six pages, relationships and explicit DAX. Included execution is on synthetic fixtures; real business impact remains to be measured.

## Two-minute technical walkthrough
Start with source grains: M5 is item-store-day after unpivot; DataCo is order-line. Explain weekly-price and calendar joins and why delivery must be aggregated once per order. Describe privacy allowlisting and schema/quality failures. Show Parquet partitioning and the bounded training sample. Explain origins, the held-out test, frozen prices and recursive lag construction. Read the executed model selection and test metrics; distinguish aggregate ETS/SARIMA from item-level candidates. Show safety-stock/EOQ formulas and the separate periodic-review protection horizon. Trace opening stock plus receipts minus fulfillment to closing stock. Compare one service level, average Monte Carlo runs and state which costs are excluded. Finish with the separate BI domains, scenario guards and the evidence required before deployment.

## STAR example
**Situation:** A portfolio business scenario required visibility into fluctuating sales, inventory trade-offs and late shipments.

**Task:** Build a reproducible analytics prototype without confusing independent source datasets or invented inventory data with real operational facts.

**Action:** Implemented validation, memory-aware transformation, dimensional SQL, chronological forecasting, configurable replenishment simulation, explicit BI measures and tests. Removed PII and documented measurement limits.

**Result:** Delivered an executable repository and verified fixture results. Real-source scale is [series count], selected test WAPE [X%], and scenario cost difference [currency X] only after those values are calculated from authenticated source data. No production improvement is claimed.

## 1. Why this project?
It connects forecasting, replenishment and delivery service to decisions while demonstrating SQL, Python, dimensional modeling and BI. I chose it to show careful business definitions as well as modeling.

## 2. What business problem did you solve?
I built a reproducible decision-support prototype for demand uncertainty, inventory trade-offs and delivery/profit visibility. Real operational impact is unmeasured until deployed with actual inventory and supplier data.

## 3. How did you clean the data?
I validated source contracts, detected DataCo encoding, normalized columns/categories, parsed dates, checked keys/durations and removed all non-allowlisted customer fields. Invalid financial rows are flagged; critical key/date conflicts fail.

## 4. Why PostgreSQL?
It supplies stable dimensional contracts, primary/foreign keys, indexed SQL serving tables and familiar BI connectivity. DuckDB handles local bulk transformation; each engine has a defined role.

## 5. Why DuckDB and Parquet?
M5 wide-to-long expansion is large. DuckDB can scan CSV and spill transformations without loading the entire panel into Pandas. Partitioned Parquet is columnar, typed and reusable for analytics.

## 6. How did you prevent leakage?
I selected the cohort before validation, shifted rolling windows, learned category vocabularies on training, froze future price and recursively appended predictions. Inventory evaluation assumptions and segment labels are derived before test origin.

## 7. Why time-based validation?
Future demand is the deployment target. Random splits share nearby observations and can leak future patterns; rolling origins preserve causal time order and expose regime differences.

## 8. Which model won?
Read selected_model from run_manifest.json and its held-out WAPE from forecast_model_metrics. The winner is chosen on the selection fold, not the test. I would never assert LightGBM won without those numbers.

## 9. How did you evaluate accuracy?
MAE/RMSE show unit errors; WAPE aggregates absolute error relative to demand; bias shows direction; pooled bottom-level RMSSE scales by training variability. Segment and interval coverage diagnostics expose uneven performance.

## 10. Why can MAPE mislead?
It is undefined at zero actual demand and disproportionately weights small denominators. I report nonzero-only MAPE as secondary and favor WAPE/MAE with explicit null-denominator behavior.

## 11. How did you calculate safety stock?
I used z times the square root of lead-time days times forecast-error variance plus mean daily demand squared times lead-time variance. It assumes independence and an approximate normal distribution.

## 12. How did you determine reorder points?
Expected demand during lead time plus safety stock is the reference ROP. The implemented weekly review additionally protects the review period and accounts for stock already on order.

## 13. What assumptions did you make?
Inventory, lead times, costs, case packs and lost-sale penalties are simulated with seed 42, configurable defaults and sensitivity cases. The assumption table is explicitly not Walmart data.

## 14. Why keep M5 and DataCo separate?
They describe different businesses and have no verified common transaction keys. I share an executive layout, not fabricated joins or combined financial totals.

## 15. How would you deploy?
Version inputs/config/model artifacts, orchestrate idempotent daily jobs, load a read-only BI serving database transactionally, add data freshness/quality alerts and monitor forecast errors and service against targets.

## 16. What would real inventory and supplier data change?
I would estimate lead-time distributions, reconcile inventory positions including open POs, distinguish censored sales from demand, use actual landed costs and constrain replenishment by capacity and shelf life.

## 17. How would you monitor drift?
Track rolling WAPE, signed bias and interval coverage by store/category, plus feature distributions and missingness. Compare to a seasonal baseline and retrain only under a controlled, time-based evaluation.

## 18. Hardest technical problem?
Keeping multi-step forecasting honest while combining a large panel with inventory decisions. One-step validation can look excellent but silently use tomorrow’s sales. Recursive prediction and boundary tests address that risk.

## 19. Which recommendation had greatest impact?
Use the ranked evidence in the executed real-data report. Before real-source execution there is no defensible impact ranking. Scenario cost differences are hypotheses for a pilot, not achieved savings.

## 20. What would you improve next?
Add real availability and procurement feeds, intermittent-demand methods, forecast reconciliation, segment-calibrated intervals, drift monitoring and a larger paired simulation with burn-in and terminal stock valuation.
