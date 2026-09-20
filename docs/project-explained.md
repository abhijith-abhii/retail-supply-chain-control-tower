# Understand the Retail Supply Chain Control Tower

This is a study guide to repository snapshot **0b85891**, read on 18 September 2026. It explains the code as written, including its trade-offs. Reasons describe the design's function and rationale; they do not mean every constant was empirically optimized or every choice is mandatory.

The companion annotated reference includes every Python source/test line, SQL statement, primary configuration setting, dependency/setup file, notebook code cell and DAX measure. Related lines share an explanation when they form one expression, query or output template. Blank separators and closing delimiters have no independent business logic. Raw CSV records, generated reports, generated dictionaries, notebook execution outputs and visual theme values are data/documentation rather than additional algorithms.

## 1. What business problem does this solve?

A retailer needs to decide what is likely to sell, how much stock to carry and where operations lose service or profit. Buying too little loses sales; buying too much ties up money and creates holding costs. Delivery performance adds another service question, and profitability tells us whether revenue is actually contributing profit.

The project is a reproducible analytical pipeline: it reads files, validates them, builds analytical tables, runs forecasts and inventory scenarios, and exports evidence for reports/Power BI. It is not a deployed ordering system, a live warehouse application or a finished Power BI file. It does not place purchase orders.

There are five business questions: what sold and where; what may sell over the next 28 days; which stock policies might balance service and cost; which orders were late relative to their promise; and which products/categories/orders have low profit. Different questions require different data grains and different evidence.

## 2. Why are there two datasets?

M5 supplies item/store daily sales, a calendar and weekly prices. These support retail forecasting. DataCo supplies independent order lines, shipping information and profit fields. These support logistics and profitability analysis.

They do not describe the same transactions, customers or product catalog. Similar dates, category labels or locations do not create a valid join key. The code therefore keeps their facts and business measures separate. You can show both domains on one executive page; you cannot claim that DataCo delays caused Walmart sales changes or add the two domains' money into one company total.

M5 does not provide verified opening inventory, supplier lead times, acquisition costs or open purchase orders. The project creates clearly labeled assumptions for these. Consequently its inventory results are simulated scenarios. The delivered executed examples use generated synthetic data as well, so even historical-looking fixture sales/delivery figures are demonstration results.

## 3. Understand the grain before understanding the formulas

Grain means what one row represents. In sales_daily it is one product in one store on one date. In demand_forecasts_28d it is that pair's forecast for one target date from one origin/model. In DataCo profitability it is one order line; in delivery performance it is one whole order. In inventory simulation it is one pair/day/policy/scenario/service/run.

Suppose order 101 has three lines and is late, while order 102 has one line and is on time. Counting lines gives 3/4=75% late; counting orders gives 1/2=50%, the intended order-level metric. However, profit must first sum the legitimate line amounts. This is why the project intentionally maintains two DataCo tables.

Suppose the same initial inventory appears under 90%, 95% and 98% service scenarios. Summing all three multiplies stock by three even though they represent alternative policies. Likewise, three simulated runs are three possible worlds, not three months of business. Aggregate within a run, then average runs, while selecting a comparable policy/service/scenario.

## 4. What happens when you run the command?

The command python src/run_pipeline.py --mode sample --fixture starts the main orchestration function. It reads config, prepares output folders and generates deterministic demonstration inputs. It opens DuckDB, creates source views, validates keys/values and produces audit summaries. It converts M5's wide daily columns into long daily rows, joins calendar/prices and selects a pre-evaluation cohort.

It then creates past-only model features, cleans DataCo and exports descriptive dimensions/trends. It compares forecast candidates on chronological windows, selects one before the final test, evaluates that selected model and forecasts the next 28 dates. It constructs simulated inventory assumptions, derives alternative policies, replays baseline versus forecast-based ordering and varies assumptions in sensitivity cases.

Finally it exports CSV/Parquet, recommendations, reports/charts, a field dictionary and a run manifest. PostgreSQL loading happens only with --load-postgres. Notebook code reads these exports; it does not independently repeat all model training. Power BI specifications describe a further dashboard-build step.

## 5. Why this folder and tool structure?

The src/ingestion modules handle external file shape/encoding; validation checks contracts; transformation establishes clean grains; forecasting predicts; inventory evaluates stock decisions; operations analyzes delivery/profit; reporting packages evidence. This separation makes a changed CSV format less likely to require rewriting an inventory formula, and makes a forecasting feature testable without running the database.

Python coordinates the work and handles models/simulations. Pandas is convenient for smaller tables and labeled transformations. NumPy provides numerical arrays/random draws. DuckDB expresses joins/window calculations over large CSV/Parquet sources. Parquet preserves types and supports column-oriented analytical reads; CSV is convenient for inspection but larger and less type-safe. PostgreSQL is an optional relational serving layer with keys/constraints and reusable SQL views. Power BI consumes the analytical outputs and defines filtered measures.

These are engineering trade-offs, not the only possible stack. Spark/distributed processing is not implemented. Full-data scale has not been benchmarked here. Chunked CSV parsing does not guarantee low total memory when chunks are concatenated; prediction batches likewise do not prevent the final result list from growing.

## 6. Why validate rather than quietly clean everything?

Missing keys, repeated price keys or duplicate dates can multiply join rows and corrupt totals. Negative demand is invalid under this project's data contract. Missing price on positive sales makes the revenue proxy unreliable. The code therefore rejects these cases instead of continuing with attractive but wrong charts.

Not every unusual value is an error. Negative profit can represent a real loss. Large demand on a festival may be legitimate. The audit records missingness, ranges, duplicates and a sampled outlier screen; it does not blindly remove outliers. For DataCo, contradictory shipment fields within one order trigger a failure rather than arbitrarily choosing whichever line appears first.

Unknown and zero have different meanings. Missing profit remains NaN/NULL; zero profit means known break-even. A zero-sales day is retained as observed zero, not dropped. Undefined ratios use missing/blank values rather than reporting a misleading 0%.

## 7. Why reshape M5 and join prices this way?

The source has d_1, d_2 and hundreds/thousands of other day columns. UNPIVOT makes date a row attribute, allowing ordinary date filters, groupby, SQL windows and one shared model input structure. Each daily row matches calendar d, and then weekly price matches item_id + store_id + wm_yr_wk. Joining on item alone would attach other stores/weeks and multiply or misprice sales.

Revenue is recorded units multiplied by listed weekly selling price. It is not guaranteed accounting net revenue: promotions, returns, taxes and other adjustments may not be represented. Recorded sales also may understate true demand if availability was constrained. The project cannot recover unobserved lost demand from M5 alone.

## 8. Why explore trends and classify products?

Daily/weekly/monthly trends reveal different patterns and help check whether inputs make sense before trusting a model. Store/category summaries identify concentration. Event/SNAP comparisons are descriptive signals; they do not prove causal promotion effects. Price-demand correlation is also associational and can be distorted by product mix, timing and demand-driven pricing.

ABC ranks recent revenue contribution using approximately 80% and 95% cumulative boundaries. The boundary-crossing item stays in the higher class. XYZ uses coefficient of variation (standard deviation divided by mean) plus zero-demand frequency. A-X suggests revenue importance and relative predictability; C-Z suggests lower contribution and irregular demand. These labels help prioritize review, but thresholds are configurable heuristics rather than universally optimal stocking strategies.

The Python classifications use a trailing 90-day summary. Some standalone SQL interview examples use all loaded history or item-only aggregation. The guide flags those distinctions; they should not be expected to produce identical classifications without aligning grain and date scope.

## 9. Why time-based forecasting tests?

A forecast must be constructed from information available before its target dates. A random row split can put future observations into the model that predicts the past. The project instead advances forecast origins chronologically. This principle follows established time-series evaluation practice; see [Forecasting: Principles and Practice, accuracy evaluation](https://otexts.com/fpp2/accuracy.html).

With the fixture's 600 observed days and default three 28-day windows: sample selection ends at day 516; calibration predicts 517–544; selection predicts 545–572; locked testing predicts 573–600; final production prediction covers 601–628. The actual calendar dates come from input. Training at each origin uses up to the trailing 365 available days, subject to a row cap.

Calibration residuals create test uncertainty bands; the selection window chooses the model; the last window measures its later performance. Reusing the last test to choose the winner would undermine its independence. One selection and one test window still provide limited evidence across different seasons/regimes.

## 10. Why these forecast features and models?

Lags 1/7/14/28/56 represent yesterday and repeated weekly intervals. Rolling 7/28/56-day means summarize demand level; standard deviations summarize recent variability. Day/week/month/quarter and known events encode calendar patterns. Product/store/category metadata let one global model learn shared behavior across series. Days since last positive sale helps describe intermittency.

Rolling demand windows end at one day before the target. Otherwise today's units would influence a predictor intended to predict today's units. The code's tests deliberately change future/current targets and require historical predictors and forecasts to remain unchanged.

Four baselines are deliberately simple: persist the last value, repeat the last week, repeat the last 28 days, or repeat the trailing mean. LightGBM is a candidate, not an assumed winner. Its boosted trees can model nonlinear interactions across pooled series; the selected Poisson objective is a count-oriented loss supported by [LightGBM's parameter documentation](https://lightgbm.readthedocs.io/en/stable/Parameters.html). The repository pins LightGBM 4.6.0; the linked stable documentation may describe a newer release. Tree count, leaves and learning rate are fixed project defaults, not proven best hyperparameters.

ETS and SARIMA provide classical aggregate diagnostics. Because they predict total portfolio demand here, their errors are labeled at a different grain and they cannot directly replace item-store forecasts. Aggregation permits errors across products to cancel; a smaller aggregate error is not evidence of better item-level replenishment.

For day two onward, LightGBM uses its own earlier predictions as lag history. This recursion prevents reading held-out actuals, but errors can accumulate. Future price is frozen at the last known value because an unprovided future price schedule cannot legitimately be used. Training still sees actual historical prices, so prediction-time price assumptions deserve attention.

## 11. Why several accuracy metrics?

Let actual demand be [10, 0, 20] and forecast be [12, 3, 18]. Signed errors are [2, 3, −2], and absolute errors are [2, 3, 2]. MAE is 7/3≈2.33 units. RMSE is sqrt(17/3)≈2.38 units and penalizes large errors more strongly. WAPE is 7/30≈23.33%; normalized bias is 3/30=10%, indicating overall overforecasting.

MAPE uses only nonzero actual days here: (2/10+2/20)/2=15%. That excludes the false positive forecast of 3 on the zero-demand day, illustrating why MAPE alone is insufficient. WAPE remains defined when some days are zero, but not when total actual demand is zero.

RMSSE scales squared errors using training-history first differences after leading zeros. Constant/all-zero histories have undefined scale. This project pools normalized bottom-level errors; it does not implement the official M5 hierarchical weighted WRMSSE score.

No metric alone answers whether an inventory decision is useful. Two models with similar WAPE can have different underforecasting patterns, and stock costs/service consequences can differ.

## 12. What do 80% and 95% intervals mean here?

The code takes earlier actual-minus-prediction residual quantiles separately for each forecast horizon, pools across series, and adds those offsets to point predictions. It clips negative demand and expands bounds if necessary to contain the point forecast.

These are approximate empirical bands. A label of 95% does not guarantee that 95% of future outcomes fall inside them. The project measures coverage on held-out data and reports shortfalls. Pooling different demand scales, small samples, temporal changes and recursive error can all limit calibration. Adding item-level interval limits does not automatically produce a valid portfolio interval because joint uncertainty/dependence matters.

## 13. Why the inventory equations?

The safety-stock approximation is z(service) × sqrt(L×σ² + μ²×σL²), where μ is expected daily demand, σ is demand/forecast-error uncertainty, L is mean lead days and σL is lead-time standard deviation. The first term represents demand variation during replenishment; the second represents uncertain delivery duration. The code assumes independence and a usable normal approximation; autocorrelation/intermittency/bias can invalidate this simplification.

For μ=10, σ=3, L=7, σL=2 and service 95%, safety stock is approximately 35.4 units. Expected lead-time demand is 70, so reorder point is about 105.4. A periodic-review policy also covers the review interval R, using demand over L+R and its protection safety stock.

EOQ = sqrt(2DS/H), with annual demand D, fixed order cost S and annual holding cost per unit H. Larger orders reduce order frequency but carry more stock. The simulation combines EOQ with an order-up-to gap and purchasing lot constraints. This hybrid rule is called optimized in table labels, but no mathematical optimizer proves it minimizes cost for the simulated system.

MOQ and case packs matter operationally: a calculated need of seven units with six-unit cases becomes twelve units. Fractional forecasts represent expected demand; procurement quantities are rounded to feasible lots. Initial inventory, costs and lead distributions must be replaced/validated with real operational information before action.

## 14. Why simulate day by day and compare paired policies?

Daily sequence matters: receive due orders, serve demand from available stock, record lost sales, then order on review days. An order placed today arrives no earlier than tomorrow. Inventory position includes stock already on order, preventing repeated unnecessary buying. Conservation identities verify that units cannot appear or vanish.

Both policies see the same actual demand path and the same calendar-indexed lead-time random draws. This reduces random supply differences when comparing decisions. The baseline uses historical-average days cover; the alternative uses future forecast protection plus safety stock and EOQ. Three default runs randomize supply lead times, not new demand trajectories.

Fill rate is the fraction of demanded units fulfilled. Cycle service is the fraction of completed replenishment cycles without a shortage. A 95% target cycle service is not the same as a guaranteed 95% fill rate. Short replay windows may contain too few completed cycles for reliable estimates.

Total modeled inventory cost includes holding, fixed ordering and lost-sale penalty. It excludes several real-world costs/constraints, including purchase cash flow, expiry and capacity. Savings equal baseline cost minus alternative cost; a negative value is a deterioration and is retained honestly. A finite 28-day replay without full terminal-inventory valuation or warm-up may favor/penalize policies differently than long-run operations.

Sensitivity changes one factor at a time by 0.5×/1.5×. It shows which assumptions move the conclusion, but it neither models their joint probability nor exhaustively searches an optimum.

## 15. Why this delivery and profit methodology?

Late means actual shipping duration exceeds scheduled duration for an eligible order. This measures performance against the promise; a fast absolute shipment can still miss an aggressive promise. Cancelled/suspected-fraud orders and invalid durations are excluded from the late-rate denominator, not silently counted as on time. Positive delay includes zero for early/on-time orders, while signed delay retains early arrivals as negative values.

Line profit comes from a configured source column, whose additive meaning must be checked. Portfolio margin is total profit divided by total sales. For a 100-sales/10-profit line and a 10-sales/5-profit line, average line margins is 30%, while the correct combined margin is 15/110≈13.64%. This is why the code uses ratios of sums.

The optional risk model predicts late outcomes only from attributes available before delivery. Actual duration and the source late flag would give away the answer. It holds out later dates and reports multiple classification metrics. It is not enabled by default, probability-calibrated or deployed as an alert service.

## 16. Why SQL keys, views and DAX guards?

Primary keys define row identity; foreign keys stop orphan references; checks reject impossible values. Dimensions describe entities while facts store measurements at declared grains. A date-event bridge supports multiple events without duplicating the sales fact. The loader replaces owned tables in a transaction, so a failed SQL quality check rolls back the database snapshot.

Views centralize common business definitions. A materialized view stores a precomputed monthly summary for faster reads but needs refresh. Indexes trade storage/write effort for potential query speed; query plans and real workloads must verify that benefit. The supplied SQL interview examples demonstrate joins, windows, CTEs and aggregation, not a complete production query-tuning study.

DAX measures recalculate under dashboard filters. CALCULATE changes filter context, as described in [Microsoft's CALCULATE documentation](https://learn.microsoft.com/en-us/dax/calculate-function-dax). DIVIDE returns blank for an unavailable denominator here. HASONEVALUE guards against combining scenarios. AVERAGEX over run IDs averages simulations. TREATAS passes a selected set of order IDs to the delivery fact for category analysis without a broad bidirectional relationship that could double count.

The DAX catalogue is a specification, not proof of successful execution in Power BI Desktop. A native PBIX and visual reconciliation still need to be built/tested on the target environment.

## 17. What does your test result establish?

Your 18 passed, 1 skipped means the collected tests that ran passed; it is not a forecast accuracy percentage. In this source snapshot the PostgreSQL integration test skips when TEST_DATABASE_URL is absent. python -m pytest -q -rs prints the actual skip reason in your environment.

Tests check schema/key rejection, privacy sentinels, line/order counts, no-future-information properties, metric edge cases, inventory conservation and output alignment. They do not establish real-world savings, prove all possible data errors are handled, guarantee interval coverage or validate a native Power BI dashboard. Some integration tests consume already-generated fixture outputs, so the pipeline should be run before them.

## 18. Choices to understand rather than blindly defend

The code often packs multiple statements onto one physical line with semicolons. That saves vertical space, not computation. Splitting them would improve readability and debugging. Some imports, parameters and return assignments are unused; they are cleanup opportunities, not intentional analytical mechanisms.

Config assertions can be disabled by Python optimization; explicit validation would be stronger. Reports/recommendations hard-code .95 and assume nonempty groups. price_future_policy is not a selectable strategy in code. DataCo order_id nulls are not explicitly rejected before grouping. DataCo monthly summaries and profit summaries differ in their treatment of flagged invalid rows/all-missing sums. Some source calendar fields consumed later are missing from the early required-column list.

Forecast settings/ABC-XYZ cutoffs are fixed heuristics, not tuned optima. Safety-stock assumptions omit dependence and forecast bias handling. Recursive positive predictions can weaken an intermittency feature. Simulation uses small deterministic cohorts, few lead-time repetitions, finite horizons and no terminal-stock accounting. The real-data full run and native BI engine remain unverified.

The loader is a snapshot replacement, not a database migration or incremental historical warehouse. Model objects are not saved for separate serving. File exports can be partial on a failed run, unlike the later database transaction. These are limitations of the current implementation, not changes made by this guide.

## 19. How to read the line reference

Start with run_pipeline.py to understand the sequence, then follow ingestion → transformation → features → evaluation → inventory → operations → reporting. Read helper modules when their calls appear. Read tests beside the corresponding function to see the expected invariant. Finish with database/SQL and DAX, which consume the outputs.

Common Python vocabulary: def creates a function; return hands back a result; import makes existing functionality available; for repeats work; if selects a branch; raise stops on an invalid condition; with manages a resource/transaction; a dictionary maps names to values; a list accumulates ordered items. A DataFrame is a labeled table. groupby collects rows sharing keys, agg summarizes them and merge joins tables. validate on merge checks the expected join cardinality. copy prevents later edits from unintentionally changing the original object. An f-string inserts values into text, often for paths, labels and controlled SQL.

Common SQL vocabulary: SELECT chooses/computes columns; WHERE filters rows before aggregation; GROUP BY sets summary grain; HAVING filters completed groups; JOIN combines matching records; LEFT JOIN preserves left records even without a match; OVER defines a window calculation while keeping rows; PARTITION BY separates series; ORDER BY defines sequence; NULLIF avoids an invalid zero denominator; UNION ALL stacks rows without deduplicating them.

For each annotated span, read the displayed source and its explanation together. Exact line numbers refer to the snapshot above and may move if the repository changes. This guide explains the executable project at source snapshot 0b85891; it does not change its analytical behavior.


# Annotated code reference


## src/run_pipeline.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  """CLI orchestration. No credentials required for local files; --load-postgres is explicit."""
```

Documents the entry point and the explicit database opt-in; the local demonstration needs no database credentials.


### Line 2

```text
  2  import sys
```

Import sys from sys to provide Python interpreter settings, here the import search path.


### Line 3

```text
  3  from pathlib import Path
```

Import Path from pathlib to provide portable filesystem paths; it avoids hard-coding slash separators and supports repository-relative locations.


### Line 4

```text
  4  if __package__ in (None,''): sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
```

When launched as a file, add the repository root to Python's import search path so imports such as src.config resolve. Running as an installed package would make this workaround unnecessary.


### Line 5

```text
  5  import argparse
```

Import argparse from argparse to provide command-line flags and argument validation.


### Line 6

```text
  6  import logging
```

Import logging from logging to provide timestamped progress messages.


### Line 7

```text
  7  import shutil
```

Import shutil from shutil to provide filesystem operations, here removal of owned generated directories before rebuilding.


### Line 8

```text
  8  import time
```

Import time from time to provide elapsed-time measurement with a monotonic performance counter.


### Line 9

```text
  9  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws. The imported name(s) numpy are not referenced elsewhere in this module’s executable syntax; they are cleanup opportunities rather than needed logic here.


### Line 10

```text
 10  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 11

```text
 11  import duckdb
```

Import duckdb from duckdb to provide local SQL queries over CSV/Parquet and analytical window calculations.


### Line 12

```text
 12  from src.config import ROOT,load_config
```

Import ROOT, load_config from src.config to provide reuse src/config.py rather than duplicating that stage’s implementation.


### Line 13

```text
 13  from src.logging_config import configure_logging
```

Import configure_logging from src.logging_config to provide reuse src/logging_config.py rather than duplicating that stage’s implementation.


### Line 14

```text
 14  from src.fixtures import create_fixture
```

Import create_fixture from src.fixtures to provide reuse src/fixtures.py rather than duplicating that stage’s implementation.


### Line 15

```text
 15  from src.ingestion.load_m5 import load_m5
```

Import load_m5 from src.ingestion.load_m5 to provide reuse src/ingestion/load_m5.py rather than duplicating that stage’s implementation.


### Line 16

```text
 16  from src.ingestion.load_dataco import load_dataco
```

Import load_dataco from src.ingestion.load_dataco to provide reuse src/ingestion/load_dataco.py rather than duplicating that stage’s implementation.


### Line 17

```text
 17  from src.validation.data_quality import audit_csv,validate_m5
```

Import audit_csv, validate_m5 from src.validation.data_quality to provide reuse src/validation/data_quality.py rather than duplicating that stage’s implementation.


### Line 18

```text
 18  from src.transformation.transform_m5 import transform_m5
```

Import transform_m5 from src.transformation.transform_m5 to provide reuse src/transformation/transform_m5.py rather than duplicating that stage’s implementation.


### Line 19

```text
 19  from src.transformation.transform_dataco import transform_dataco
```

Import transform_dataco from src.transformation.transform_dataco to provide reuse src/transformation/transform_dataco.py rather than duplicating that stage’s implementation.


### Line 20

```text
 20  from src.transformation.build_dimensions import build_dimensions
```

Import build_dimensions from src.transformation.build_dimensions to provide reuse src/transformation/build_dimensions.py rather than duplicating that stage’s implementation.


### Line 21

```text
 21  from src.forecasting.feature_engineering import create_feature_view
```

Import create_feature_view from src.forecasting.feature_engineering to provide reuse src/forecasting/feature_engineering.py rather than duplicating that stage’s implementation.


### Line 22

```text
 22  from src.forecasting.evaluate_models import evaluate_models,add_intervals,segment_metrics
```

Import evaluate_models, add_intervals, segment_metrics from src.forecasting.evaluate_models to provide reuse src/forecasting/evaluate_models.py rather than duplicating that stage’s implementation.


### Line 23

```text
 23  from src.forecasting.train_models import train_global
```

Import train_global from src.forecasting.train_models to provide reuse src/forecasting/train_models.py rather than duplicating that stage’s implementation.


### Line 24

```text
 24  from src.forecasting.generate_forecasts import predict_origin
```

Import predict_origin from src.forecasting.generate_forecasts to provide reuse src/forecasting/generate_forecasts.py rather than duplicating that stage’s implementation.


### Line 25

```text
 25  from src.inventory.create_assumptions import create_assumptions
```

Import create_assumptions from src.inventory.create_assumptions to provide reuse src/inventory/create_assumptions.py rather than duplicating that stage’s implementation.


### Line 26

```text
 26  from src.inventory.calculate_inventory_policy import policies
```

Import policies from src.inventory.calculate_inventory_policy to provide reuse src/inventory/calculate_inventory_policy.py rather than duplicating that stage’s implementation.


### Line 27

```text
 27  from src.inventory.inventory_simulation import simulate
```

Import simulate from src.inventory.inventory_simulation to provide reuse src/inventory/inventory_simulation.py rather than duplicating that stage’s implementation.


### Line 28

```text
 28  from src.inventory.sensitivity_analysis import sensitivity
```

Import sensitivity from src.inventory.sensitivity_analysis to provide reuse src/inventory/sensitivity_analysis.py rather than duplicating that stage’s implementation.


### Line 29

```text
 29  from src.operations.delivery_analysis import delivery_summary,category_delivery
```

Import delivery_summary, category_delivery from src.operations.delivery_analysis to provide reuse src/operations/delivery_analysis.py rather than duplicating that stage’s implementation.


### Line 30

```text
 30  from src.operations.profitability_analysis import profitability
```

Import profitability from src.operations.profitability_analysis to provide reuse src/operations/profitability_analysis.py rather than duplicating that stage’s implementation.


### Line 31

```text
 31  from src.analysis import eda,history_summary,segmentation
```

Import eda, history_summary, segmentation from src.analysis to provide reuse src/analysis.py rather than duplicating that stage’s implementation.


### Line 32

```text
 32  from src.utils.file_utils import export_frame,write_json,sql_literal
```

Import export_frame, write_json, sql_literal from src.utils.file_utils to provide reuse src/utils/file_utils.py rather than duplicating that stage’s implementation.


### Line 33

```text
 33  from src.reporting import write_reports,output_dictionary
```

Import write_reports, output_dictionary from src.reporting to provide reuse src/reporting.py rather than duplicating that stage’s implementation.


### Line 34

```text
 34
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 35

```text
 35  def run(mode='sample',fixture=False,root=ROOT,config_path=None,load_postgres=False,skip_audit=False):
```

Defines the entire workflow with defaults. Arguments distinguish small/full runs, synthetic inputs, alternate configuration and optional database loading.


### Line 36

```text
 36      root=Path(root);cfg=load_config(config_path);started=time.perf_counter();configure_logging()
```

Normalize the root path, read configuration, start elapsed-time measurement and enable progress logging. Combining four statements on one line saves space but makes debugging less clear; it is not a speed optimization.


### Line 37

```text
 37      tag='fixture' if fixture else mode
```

Assign an output label. Fixture results have their own folder, so synthetic outputs do not overwrite source-data sample/full outputs.


### Line 38

```text
 38      out=root/'data/powerbi'/tag;processed=root/'data/processed'/tag;reports=root/'reports'/tag
```

Construct export, intermediate and report locations relative to the chosen root. pathlib handles path separators.


### Line 39

```text
 39      for p in [out,processed,reports,root/'data/interim']: p.mkdir(parents=True,exist_ok=True)
```

Create required folders, including parents; repeated setup succeeds because exist_ok=True.


### Line 40–42

```text
 40      # Rebuild only owned generated run directories, avoiding stale partition mixing.
 41      if processed.exists(): shutil.rmtree(processed)
 42      processed.mkdir(parents=True)
```

Delete and recreate this run's processed directory. Partitioned exports otherwise risk mixing old partitions with new data. This is a snapshot rebuild, not an incremental pipeline; it removes generated data for the selected run.


### Line 43–44

```text
 43      for p in out.glob('*.parquet'): p.unlink()
 44      for p in out.glob('*.csv'): p.unlink()
```

Remove old CSV/Parquet exports for this run so discontinued tables cannot be mistaken for fresh results. Reports are not completely cleared, so obsolete optional report files can remain.


### Line 45

```text
 45      m5,dc=create_fixture(root/'data/sample',cfg['seed']) if fixture else (root/'data/raw/m5',root/'data/raw/dataco')
```

Choose explicitly generated fixture folders or real raw-data folders. Missing real files cause an error rather than silently substituting synthetic data.


### Line 46

```text
 46      con=duckdb.connect(str(root/'data/interim'/f'{tag}.duckdb'))
```

Open a persistent local DuckDB file named for this run. DuckDB provides SQL over CSV/Parquet without requiring a separate server.


### Line 47

```text
 47      con.execute(f"SET threads={int(cfg['threads'])}");con.execute(f"SET memory_limit={sql_literal(cfg['duckdb_memory_limit'])}")
```

Apply configured thread and memory limits. Convert threads to integer and quote the memory string before inserting trusted configuration into SQL.


### Line 48–50

```text
 48      logging.info('Loading and validating source files')
 49      load_m5(con,m5);validate_m5(con)
 50      raw_dataco,encoding=load_dataco(dc/cfg['dataco']['filename'],cfg['dataco'],reports)
```

Announce ingestion, load/validate the M5 views, then load DataCo with its encoding and privacy allowlist. Invalid core data should fail before expensive forecasting.


### Line 51–53

```text
 51      if not skip_audit:
 52          for path in sorted(m5.glob('*.csv')): audit_csv(path,reports)
 53          audit_csv(dc/cfg['dataco']['filename'],reports,encoding)
```

Unless explicitly bypassed, create descriptive audits for every M5 CSV and the DataCo CSV. Audits describe data; they do not silently delete outliers. Their runtime can be considerable for full M5.


### Line 54

```text
 54      cohort_cutoff=transform_m5(con,cfg,mode,processed/'sales_daily')
```

Convert M5 to daily item-store data and select the sample using only the period before evaluation. Save the cutoff for provenance.


### Line 55

```text
 55      create_feature_view(con)
```

Define lagged forecasting features once as a SQL view; training queries reuse the same definitions.


### Line 56–58

```text
 56      history_days=con.execute('SELECT min(n) FROM (SELECT count(*) n FROM sales GROUP BY item_id,store_id)').fetchone()[0]
 57      needed=max(28,cfg['inventory']['simulation_days'])*cfg['backtest_folds']+cfg['minimum_history_days']
 58      if history_days<needed: raise ValueError(f'Need at least {needed} daily observations per series')
```

Measure the shortest series, compute history needed for all chronological evaluation windows plus the minimum training period, and stop if insufficient. With defaults: 28×3+180=264 days; 90-day replay needs 450.


### Line 59–61

```text
 59      # Large sales exports stream through DuckDB, not Pandas.
 60      con.execute(f"COPY sales TO {sql_literal(out/'sales_daily.parquet')} (FORMAT PARQUET)")
 61      con.execute(f"COPY features TO {sql_literal(processed/'forecast_features.parquet')} (FORMAT PARQUET)")
```

Stream daily sales and feature tables from DuckDB to Parquet rather than building a huge Pandas frame. The feature table includes historical targets; training still restricts dates and predictor columns.


### Line 62

```text
 62      lines,delivery=transform_dataco(raw_dataco,cfg['dataco'],reports)
```

Separate cleaned DataCo lines from one-row-per-order delivery records. These have different analytical denominators.


### Line 63–66

```text
 63      export_frame(lines,'dataco_profitability',out);export_frame(delivery,'dataco_delivery_performance',out)
 64      ship=delivery_summary(delivery);export_frame(ship,'dataco_shipping_mode_performance',out)
 65      export_frame(category_delivery(lines,delivery),'dataco_category_delivery',out)
 66      profit,orders=profitability(lines);export_frame(profit,'dataco_profitability_summary',out);export_frame(orders,'dataco_order_profit',out)
```

Export detailed and summarized delivery/profit tables. One source frame can support several views, but their totals must not be added together as if they were separate transactions.


### Line 67

```text
 67      dims=build_dimensions(con,lines,delivery,out);tables=eda(con,lines,delivery,cfg,out)
```

Build descriptive dimension tables and exploratory summaries. The returned dims/tables variables are unused later; the relevant side effect is their exports.


### Line 68–71

```text
 68      logging.info('Rolling-origin model comparison')
 69      backtest,comparison,test,champion=evaluate_models(con,cfg)
 70      export_frame(backtest,'forecast_backtest_all',out);export_frame(test,'forecast_backtest_selected',out)
 71      export_frame(comparison,'forecast_model_metrics',out)
```

Run chronological model comparisons and export all candidates, the chosen model's locked test, and aggregate scores. Retaining all candidates makes the selection auditable.


### Line 72–74

```text
 72      # Segment labels are frozen at final test origin, never recomputed with held-out demand.
 73      test_origin=test.origin.iloc[0];pretest=history_summary(con,test_origin)
 74      export_frame(segment_metrics(test,segmentation(pretest,cfg)),'forecast_accuracy_by_segment',out)
```

Compute segmentation using only history available at the test origin, then summarize test accuracy by segment. Using labels calculated after the test would leak held-out information into the evaluation groups.


### Line 75–77

```text
 75      end=con.execute('SELECT max(date) FROM sales').fetchone()[0]
 76      model,levels,_=train_global(con,end,cfg) if champion=='lightgbm' else (None,None,0)
 77      future=predict_origin(con,end,28,[champion],cfg,model,levels)
```

Find the final observed date, retrain LightGBM on available history only if it won, and forecast exactly the next 28 days. Baseline winners need no fitted model object.


### Line 78–79

```text
 78      selected_errors=backtest[(backtest.model==champion)&(backtest.fold<cfg['backtest_folds'])]
 79      future=add_intervals(future,selected_errors);export_frame(future,'demand_forecasts_28d',out)
```

Use the selected model's earlier, non-test residuals for future intervals. Excluding the last fold preserves the held-out test convention, though the final forecast could legitimately use more observed errors in a separately designed production calibration.


### Line 80–81

```text
 80      logging.info('Calculating simulated inventory policies and paired replenishment scenarios')
 81      current=history_summary(con,end);assumptions=create_assumptions(current,cfg)
```

Create current 90-day history summaries and explicitly simulated inventory inputs. The retailer datasets do not supply actual stock, supplier lead times or procurement costs.


### Line 82–90

```text
 82      # Preserve user-supplied real-run assumptions; fixture never reads real assumption files.
 83      assumption_path=root/'config/inventory_assumptions.csv'
 84      if not fixture and assumption_path.exists():
 85          supplied=pd.read_csv(assumption_path)
 86          if len(supplied):
 87              if supplied.duplicated(['item_id','store_id']).any(): raise ValueError('Duplicate inventory assumptions')
 88              assumptions=assumptions.set_index(['item_id','store_id'])
 89              supplied=supplied.set_index(['item_id','store_id']);assumptions.update(supplied);assumptions=assumptions.reset_index()
 90      if not fixture: assumptions.to_csv(assumption_path,index=False)
```

For real runs, merge saved per-item assumptions into generated defaults, reject duplicate item-store overrides, and persist the resulting table. Only matching item-store keys update. Fixture runs never read these overrides. Historical evaluation below still regenerates simulated assumptions rather than using these current overrides.


### Line 91–94

```text
 91      export_frame(assumptions,'inventory_assumptions',out)
 92      policy=policies(current,future,assumptions,selected_errors,cfg['inventory']['service_levels'],end)
 93      export_frame(policy,'inventory_policy_recommendations',out)
 94      export_frame(policy,'stockout_risk',out);export_frame(policy[policy.excess_units>0],'excess_inventory',out)
```

Export assumptions and policies for each service level; expose stock risk and excess subsets for BI. stockout_risk here includes every policy row, whereas the SQL mart filters to above-threshold risk.


### Line 95–97

```text
 95      # Historical evaluation recreates assumptions at its origin; no future prices or demand used.
 96      sim_assumptions=create_assumptions(pretest,cfg)
 97      sim_policy=policies(pretest,test,sim_assumptions,selected_errors,cfg['inventory']['service_levels'],test_origin)
```

Rebuild simulation assumptions and policy at the test origin so the replay does not use end-of-test inventory inputs or price summaries. The policy uncertainty uses earlier residuals.


### Line 98–100

```text
 98      limit=cfg['inventory'].get('simulation_series_limit',100)
 99      sim_keys=pretest.sort_values(['item_id','store_id']).head(limit)[['item_id','store_id']]
100      sim_test=test.merge(sim_keys);sim_policy=sim_policy.merge(sim_keys)
```

Cap the replay cohort for runtime, choose keys deterministically, and restrict test forecasts/policies to them. This alphabetical subset is not a representative probability sample; the manifest records its size.


### Line 101–104

```text
101      daily,kpis=simulate(sim_test,sim_policy,cfg)
102      export_frame(daily,'inventory_simulation_daily',out);export_frame(kpis,'inventory_simulation_kpis',out)
103      sens=sensitivity(pretest,test,sim_assumptions,selected_errors,sim_test,cfg,test_origin)
104      export_frame(sens,'inventory_sensitivity',out)
```

Replay paired policies, export daily balances and summary KPIs, then rerun one-factor sensitivity scenarios. The sensitivity table may cover fewer series than the base simulation.


### Line 105–110

```text
105      # Executive metrics remain separately labelled, with compatible denominators.
106      observed=con.execute('SELECT sum(units_sold) units,sum(revenue) revenue FROM sales').fetchone()
107      k=kpis[(kpis.policy=='optimized')&(kpis.target_service_level==cfg['inventory']['default_service_level'])]
108      exec_rows=[('M5','historical','total_units',observed[0]),('M5','historical','revenue',observed[1]),('M5','forecast','forecast_28d_units',future.forecast_units.sum()),
109        ('M5','scenario_estimate','estimated_cost_reduction',k.groupby('run_id').estimated_cost_reduction.sum().mean()),
110        ('DataCo','historical','eligible_order_late_rate',delivery.loc[delivery.delivery_eligible,'late_order'].mean()),('DataCo','historical','profit',orders.profit.sum(min_count=1))]
```

Build labeled executive metrics: observed M5 units/revenue, future units, average modeled savings, and separate DataCo late rate/profit. Costs are summed within each simulated world and then averaged across runs; domains and metric types remain separate.


### Line 111–112

```text
111      executive=pd.DataFrame(exec_rows,columns=['domain','metric_type','metric','value']);executive['data_provenance']='synthetic_fixture' if fixture else 'kaggle'
112      export_frame(executive,'executive_kpis',out)
```

Attach data provenance and export the executive table. A synthetic run must never become an unlabeled business result.


### Line 113–115

```text
113      if cfg['dataco']['risk_model']:
114          from src.operations.delivery_risk_model import delivery_risk
115          risk,importance=delivery_risk(delivery,cfg['seed']);export_frame(risk,'delivery_risk_metrics',out);export_frame(importance,'delivery_risk_feature_importance',out)
```

Run delivery-risk classifiers only when enabled. The local import defers loading this optional workflow; it is disabled by default.


### Line 116

```text
116      export_frame(pd.DataFrame({'last_refresh_utc':[pd.Timestamp.now(tz='UTC').isoformat()],'data_provenance':['synthetic_fixture' if fixture else 'kaggle'],'mode':[mode]}),'refresh_metadata',out)
```

Write a UTC refresh timestamp, provenance and mode. It marks when this export was generated, not when a dashboard is viewed.


### Line 117–119

```text
117      from src.recommendations import recommendations
118      export_frame(recommendations(out,fixture),'recommendations',out)
119      write_reports(out,reports,mode,fixture,champion,comparison,test,kpis,ship,policy);output_dictionary(out,root)
```

Generate evidence-linked recommendations, reports, charts and a dictionary from actual output schemas. The dictionary writes into config/docs even for a fixture run.


### Line 120–122

```text
120      if load_postgres:
121          from src.database import load_database
122          load_database(out,root/'sql')
```

If explicitly requested, load the generated snapshot into PostgreSQL. This operation replaces the project's owned database tables; it is not needed for the file-only demo.


### Line 123–126

```text
123      manifest={'mode':mode,'fixture':fixture,'selected_model':champion,'cohort_selection_cutoff':str(cohort_cutoff),'postgres_loaded':load_postgres,
124        'source_sales_rows':con.execute('SELECT count(*) FROM sales').fetchone()[0], 'forecast_rows':len(future),'simulation_series':len(sim_keys),
125        'audits_executed':not skip_audit,'elapsed_seconds':time.perf_counter()-started,'output_dir':str(out),'config':cfg}
126      write_json(reports/'run_manifest.json',manifest);con.close();logging.info('Pipeline complete: %s',out)
```

Record configuration, scope, row counts, audit status and elapsed time; save JSON, close DuckDB and log completion. An exception before this point can leave partial file exports and no final manifest because file output is not transactional.


### Line 127

```text
127      return manifest
```

Return the manifest to callers so notebooks/scripts can inspect the run without rereading console text.


### Line 128

```text
128
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 129

```text
129  if __name__=='__main__':
```

Run the CLI only when this module is executed directly; importing run does not start the pipeline.


### Line 130

```text
130      p=argparse.ArgumentParser();p.add_argument('--mode',choices=['sample','full'],default='sample');p.add_argument('--fixture',action='store_true');p.add_argument('--config');p.add_argument('--load-postgres',action='store_true');p.add_argument('--skip-audit',action='store_true',help='Explicit development-only bypass; recorded in manifest')
```

Declare command-line flags and their accepted values. action='store_true' means presence of a flag turns it on. The many declarations on one line are compact formatting, not required architecture.


### Line 131

```text
131      args=p.parse_args();run(args.mode,args.fixture,config_path=args.config,load_postgres=args.load_postgres,skip_audit=args.skip_audit)
```

Parse the command line and pass values into run. The same run function is reusable programmatically.


## config/project_config.yaml

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  seed: 42
```

Seed 42 makes fixture data and random simulation draws reproducible within this implementation. The numeric value itself has no analytical significance.


### Line 2

```text
  2  threads: 4
```

Use four threads for DuckDB/forecast model work as a laptop compromise. More threads are not always faster and some optional classifier code uses its own fixed thread count.


### Line 3

```text
  3  duckdb_memory_limit: 2GB
```

Set DuckDB's engine memory limit to 2 GB. This does not cap Pandas, model, Python output-list or total process memory.


### Line 4–5

```text
  4  sample_stores: 2
  5  sample_series: 24
```

Select up to two leading stores and 24 high-revenue item-store pairs for a manageable demonstration. These are biased toward revenue leaders, not a random representative sample.


### Line 6

```text
  6  selection_days: 90
```

Use 90 days of pre-evaluation revenue to choose the cohort. history_summary separately hard-codes 90 days and does not read this setting.


### Line 7

```text
  7  forecast_horizon: 28
```

Declare the fixed 28-day future horizon; load_config enforces it and the runner also hard-codes it.


### Line 8

```text
  8  backtest_folds: 3
```

Use three chronological folds: calibration, model selection, final test. More folds create additional calibration windows, not multiple independently selected champions.


### Line 9

```text
  9  training_days: 365
```

Use a maximum trailing 365-day training window to balance seasonal history with recency. One year does not establish reliable annual seasonality for every product.


### Line 10

```text
 10  max_training_rows: 500000
```

Cap the global model training frame at 500,000 seeded-hash-selected rows for memory/runtime. This cap does not downsample reported sales totals.


### Line 11

```text
 11  prediction_batch_series: 500
```

Predict up to 500 series together to bound each history/features batch; all forecast output records still accumulate in memory.


### Line 12

```text
 12  minimum_history_days: 180
```

Require at least 180 days before the backtest windows. The longest lag is 56 days; this buffer ensures more than the bare minimum lag history.


### Line 13

```text
 13  price_future_policy: last_observed
```

Document the last-observed-price convention. The current prediction code always implements that policy and does not branch on this text value.


### Line 14

```text
 14  xyz_cv_thresholds: [0.5, 1.0]
```

Define X/Y coefficient-of-variation cutoffs at 0.5 and 1.0; these are adjustable planning heuristics.


### Line 15

```text
 15  intermittent_zero_share: 0.5
```

Classify at least 50% zero-sale days as intermittent/Z even if CV is otherwise small.


### Line 16

```text
 16  inventory:
```

Begin nested inventory parameters; the indentation is YAML structure, not executable Python.


### Line 17

```text
 17    simulation_days: 28
```

Set the historical replay/evaluation window to 28 days; 90 is also supported but increases required history and runtime.


### Line 18

```text
 18    simulation_series_limit: 100
```

Limit base inventory simulation to 100 deterministically chosen pairs. Full-mode sales/forecasts can cover more pairs than simulation.


### Line 19

```text
 19    monte_carlo_runs: 3
```

Run three repeated lead-time paths. This is a small demonstration count, not a high-precision Monte Carlo study or demand uncertainty simulation.


### Line 20

```text
 20    service_levels: [0.90, 0.95, 0.98]
```

Compare alternative 90/95/98% assumed cycle-service targets. These are not promised achieved fill rates.


### Line 21

```text
 21    lead_time_days_range: [3, 10]
```

Draw simulated mean lead times from inclusive 3–10 days; no supplier observations establish this distribution.


### Line 22

```text
 22    lead_time_std_days: 1.5
```

Assume 1.5 days lead-time standard deviation for each pair by default.


### Line 23

```text
 23    ordering_cost: 25.0
```

Charge 25 currency units each time an order is placed; fixed order cost encourages batching in EOQ.


### Line 24

```text
 24    holding_rate: 0.25
```

Annual carrying cost equals 25% of estimated unit cost. The simulation divides this by 365 for daily end-stock cost.


### Line 25

```text
 25    cost_to_price_ratio: 0.65
```

Estimate procurement unit cost at 65% of selling price because real acquisition cost is absent.


### Line 26

```text
 26    default_service_level: 0.95
```

Choose 95% as default executive service slice. Some report/recommendation code independently hard-codes .95, so editing only this value does not update every report.


### Line 27

```text
 27    initial_days_supply: 14
```

Assume opening inventory of 14 days' recent average sales, rounded up. This is an initialization condition, not measured stock.


### Line 28

```text
 28    review_period_days: 7
```

Review replenishment every seven days; the protection window must include this delay until the next review.


### Line 29

```text
 29    lost_sale_penalty_to_price: 0.4
```

Penalize a lost unit at 40% of its selling price. This is a modeled cost, distinct from the full lost-sales revenue proxy.


### Line 30–31

```text
 30    minimum_order_quantity: 6
 31    case_pack_size: 6
```

Require positive orders to meet at least six units and a six-unit case multiple. These are simulated purchasing constraints.


### Line 32

```text
 32    baseline_days_cover: 14
```

Baseline policy aims for 14 days of historical-average demand. It is a benchmark rule, not evidence of the retailer's actual purchasing process.


### Line 33

```text
 33    sensitivity_series_limit: 24
```

Cap sensitivity scenarios at 24 pairs to keep the 13 scenario replays practical.


### Line 34

```text
 34  dataco:
```

Begin independent DataCo configuration.


### Line 35

```text
 35    filename: DataCoSupplyChainDataset.csv
```

Require this CSV filename unless explicitly changed; do not point to a data-description file accidentally.


### Line 36

```text
 36    profit_source: benefit_per_order
```

Choose normalized benefit_per_order as the intended line profit source. The implementation assumes the chosen field is additive per line; validate actual source semantics before applying to other DataCo variants.


### Line 37

```text
 37    net_sales_source: order_item_total
```

Choose order_item_total as line net sales, avoiding accidental addition of repeated order-level totals.


### Line 38

```text
 38    maximum_shipping_days: 90
```

Allow durations from 0 through 90 days for delivery eligibility. This is a plausibility rule that should be checked against business meaning.


### Line 39

```text
 39    aliases: {}
```

Optional source-column aliases after snake_case normalization support known schema variations. Empty mapping means no renaming beyond normalization.


### Line 40

```text
 40    category_mappings: {}
```

Optional category label replacements after trim/casefold support explicit standardization; they are not inferred automatically.


### Line 41

```text
 41    risk_model: false
```

Disable optional delivery-risk classification in the standard run. Turn true to fit the four pre-outcome classifiers, subject to sufficient labeled history.


## src/config.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  from pathlib import Path
```

Import Path from pathlib to provide portable filesystem paths; it avoids hard-coding slash separators and supports repository-relative locations.


### Line 2

```text
  2  import yaml
```

Import yaml from yaml to provide configuration and field definitions represented as structured YAML.


### Line 3

```text
  3  ROOT = Path(__file__).resolve().parents[1]
```

Resolve the project root from this file's location, so data paths do not depend on the shell's working directory.


### Line 4–5

```text
  4  def load_config(path=None):
  5      cfg = yaml.safe_load(Path(path or ROOT / "config/project_config.yaml").read_text())
```

Read either a supplied YAML path or the default project configuration. safe_load parses data without constructing arbitrary Python objects.


### Line 6

```text
  6      assert cfg["forecast_horizon"] == 28, "Production demand horizon must be 28 days"
```

Enforce the project's fixed 28-day production horizon. Several downstream lines also hard-code 28, so this setting is a contract rather than a fully flexible parameter.


### Line 7

```text
  7      assert cfg["backtest_folds"] >= 3
```

Require at least three windows for distinct calibration, selection and test roles.


### Line 8

```text
  8      assert cfg["inventory"]["simulation_days"] in (28, 90)
```

Allow only the implemented 28/90-day historical replay options.


### Line 9

```text
  9      assert all(0 < s < 1 for s in cfg["inventory"]["service_levels"])
```

Check probability bounds for inventory service targets. These checks use assert, which Python can disable with -O; explicit ValueError checks would be stronger configuration validation.


### Line 10

```text
 10      return cfg
```

Return the dictionary used throughout the workflow. Additional types, ranges and missing keys are not comprehensively validated here.


## src/logging_config.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import logging
```

Import logging from logging to provide timestamped progress messages.


### Line 2–3

```text
  2  def configure_logging():
  3      logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
```

Set INFO-level timestamped console logging so a long pipeline exposes its progress. basicConfig generally only configures logging when handlers have not already been installed.


## src/ingestion/load_dataco.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  from pathlib import Path
```

Import Path from pathlib to provide portable filesystem paths; it avoids hard-coding slash separators and supports repository-relative locations.


### Line 2

```text
  2  from charset_normalizer import from_bytes
```

Import from_bytes from charset_normalizer to provide a fallback guess for non-UTF8 CSV encoding.


### Line 3

```text
  3  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 4

```text
  4  from src.utils.file_utils import snake_case, write_json
```

Import snake_case, write_json from src.utils.file_utils to provide reuse src/utils/file_utils.py rather than duplicating that stage’s implementation.


### Line 5–10

```text
  5  # Explicit allowlist: unrecognized fields, customer IDs and PII never leave ingestion.
  6  ALLOWED = {"order_id","order_item_id","order_date_dateorders","shipping_date_dateorders",
  7   "days_for_shipping_real","days_for_shipment_scheduled","late_delivery_risk","delivery_status",
  8   "shipping_mode","market","order_region","category_name","customer_segment","product_name",
  9   "order_item_product_price","order_item_quantity","order_item_total","sales","benefit_per_order",
 10   "order_profit_per_order","order_item_profit_ratio","order_status","product_card_id"}
```

List permitted analytical fields rather than only blacklisting known sensitive columns. Unrecognized fields and customer identifiers are excluded. This protects named columns; it is not a general detector for sensitive text accidentally placed in a permitted field.


### Line 11

```text
 11
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 12–15

```text
 12  def load_dataco(path, cfg, report_dir):
 13      path=Path(path)
 14      if not path.exists(): raise FileNotFoundError(path)
 15      sample=path.open("rb").read(1_000_000)
```

Normalize/check the input path and read up to one million bytes to inspect encoding. An explicit with block would close this sample file handle more clearly.


### Line 16–20

```text
 16      try: sample.decode("utf-8"); encoding="utf-8"
 17      except UnicodeDecodeError:
 18          best=from_bytes(sample).best()
 19          if best is None: raise ValueError("Encoding detection failed; transcode the source explicitly")
 20          encoding=best.encoding
```

Prefer UTF-8; otherwise use charset-normalizer and reject failed detection. Encoding guesses can still be wrong and a byte sample can end in the middle of a multibyte character, so audit results matter.


### Line 21

```text
 21      chunks=[]; removed=set(); mappings=cfg.get("aliases",{})
```

Initialize cleaned chunks, dropped-column names and configurable aliases. The report records column names, not raw values.


### Line 22

```text
 22      for x in pd.read_csv(path,encoding=encoding,chunksize=50000):
```

Read 50,000 rows at a time to bound each parser batch. Because all cleaned chunks are concatenated later, total cleaned DataCo memory is not bounded.


### Line 23

```text
 23          x.columns=[mappings.get(snake_case(c),snake_case(c)) for c in x.columns]
```

Normalize messy column names and apply explicit aliases so transformations can use stable identifiers.


### Line 24

```text
 24          if x.columns.duplicated().any(): raise ValueError("Column normalization collision")
```

Reject two source names that collapse to one normalized name; otherwise the meaning of a column becomes ambiguous.


### Line 25–26

```text
 25          removed.update(set(x.columns)-ALLOWED)
 26          x=x[[c for c in x if c in ALLOWED]].copy()
```

Record discarded names and retain a copy containing only permitted fields before storing analytical data.


### Line 27–28

```text
 27          for c in x.select_dtypes(include="object"):
 28              x[c]=x[c].str.strip()
```

Strip leading/trailing whitespace in text columns to reduce accidental category splits.


### Line 29–30

```text
 29          chunks.append(x)
 30      frame=pd.concat(chunks,ignore_index=True)
```

Collect cleaned chunks and combine them with a fresh sequential row index.


### Line 31–32

```text
 31      write_json(Path(report_dir)/"dataco_ingestion.json", {"encoding":encoding,"dropped_column_names":sorted(removed),
 32        "note":"Customer identifiers and all non-allowlisted fields dropped before analytical storage."})
```

Persist an ingestion audit of the chosen encoding and removed field names, making the privacy rule inspectable.


### Line 33

```text
 33      return frame,encoding
```

Return both data and encoding so the raw-file audit can decode the same way.


## src/ingestion/load_m5.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  from pathlib import Path
```

Import Path from pathlib to provide portable filesystem paths; it avoids hard-coding slash separators and supports repository-relative locations.


### Line 2

```text
  2  from src.utils.file_utils import sql_literal
```

Import sql_literal from src.utils.file_utils to provide reuse src/utils/file_utils.py rather than duplicating that stage’s implementation.


### Line 3

```text
  3
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 4–6

```text
  4  def detect_sales(raw):
  5      for name in ("sales_train_evaluation.csv", "sales_train_validation.csv"):
  6          if (Path(raw)/name).exists(): return Path(raw)/name
```

Check the longer evaluation sales file first, then the validation file. Deterministic precedence avoids accidentally training on the shorter history when both are present.


### Line 7

```text
  7      raise FileNotFoundError(f"No M5 sales_train_evaluation.csv or sales_train_validation.csv in {raw}")
```

Fail with a useful missing-file message instead of generating invented inputs.


### Line 8–9

```text
  8  def load_m5(con, raw):
  9      raw=Path(raw); sales=detect_sales(raw)
```

Accept a DuckDB connection and source folder; normalize the folder and resolve the sales file once.


### Line 10–11

```text
 10      for name,path in {"raw_sales":sales,"calendar":raw/"calendar.csv","prices":raw/"sell_prices.csv"}.items():
 11          if not path.exists(): raise FileNotFoundError(path)
```

Map the three input files to predictable SQL view names and verify each exists.


### Line 12

```text
 12          con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_csv_auto({sql_literal(path)}, sample_size=-1)")
```

Create replaceable CSV-backed views. read_csv_auto infers types, and sample_size=-1 requests inference across the file. This can cost extra scan time but reduces inference errors from an unrepresentative initial sample.


### Line 13

```text
 13      return sales
```

Return the chosen sales path for provenance or caller inspection; the main pipeline currently ignores this return value.


## src/validation/data_quality.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  from pathlib import Path
```

Import Path from pathlib to provide portable filesystem paths; it avoids hard-coding slash separators and supports repository-relative locations.


### Line 2

```text
  2  import duckdb
```

Import duckdb from duckdb to provide local SQL queries over CSV/Parquet and analytical window calculations.


### Line 3

```text
  3  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws. The imported name(s) numpy are not referenced elsewhere in this module’s executable syntax; they are cleanup opportunities rather than needed logic here.


### Line 4

```text
  4  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 5

```text
  5  from src.utils.file_utils import sql_literal, quote_identifier, write_json, snake_case
```

Import sql_literal, quote_identifier, write_json, snake_case from src.utils.file_utils to provide reuse src/utils/file_utils.py rather than duplicating that stage’s implementation.


### Line 6

```text
  6  from src.validation.schema_validation import required_columns, require_zero
```

Import required_columns, require_zero from src.validation.schema_validation to provide reuse src/validation/schema_validation.py rather than duplicating that stage’s implementation.


### Line 7

```text
  7
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 8–10

```text
  8  def audit_csv(path, report_dir, encoding="utf-8"):
  9      """Bounded Pandas chunks plus DuckDB exact distinct/duplicate counts. No raw PII values in report."""
 10      path=Path(path); stats={}; rows=0; peak=0; decode_errors=0
```

Start a descriptive CSV audit with counters for rows, types, missingness, numeric ranges and memory. The docstring describes the intended privacy boundary.


### Line 11

```text
 11      con=duckdb.connect(); con.execute("SET memory_limit='1GB'")
```

Use a separate DuckDB connection with a 1 GB engine limit for exact distinct/duplicate counts. This is not a limit on all Python/Pandas process memory.


### Line 12–19

```text
 12      # For non-UTF8 CSV, stream a UTF8 temporary file; deleted when the audit finishes.
 13      import tempfile
 14      with tempfile.TemporaryDirectory() as td:
 15          audit_path=path
 16          if encoding.lower().replace('-','') not in ('utf8','ascii'):
 17              audit_path=Path(td)/"audit.csv"
 18              with path.open(encoding=encoding,errors="strict") as source, audit_path.open('w') as dest:
 19                  for line in source: dest.write(line)
```

For non-UTF8 input, stream a temporary UTF-8-compatible text copy in a temporary directory. Strict decoding surfaces invalid bytes. The temporary raw data may include private source fields and is deleted on normal context exit; none of its raw values are written to the report.


### Line 20

```text
 20          con.execute(f"CREATE TABLE audit AS SELECT * FROM read_csv_auto({sql_literal(audit_path)}, all_varchar=true)")
```

Load all columns as text into an audit table to preserve string forms while counting exact distinct rows/values.


### Line 21–24

```text
 21          columns=[c[0] for c in con.execute("DESCRIBE audit").fetchall()]
 22          for chunk in pd.read_csv(path,encoding=encoding,chunksize=10000):
 23              rows+=len(chunk);peak=max(peak,int(chunk.memory_usage(deep=True).sum()))
 24              for c in chunk:
```

List columns and read Pandas chunks of 10,000 rows; accumulate row counts and the largest in-memory chunk, then inspect every column.


### Line 25–27

```text
 25                  s=chunk[c]; a=stats.setdefault(c,{"dtypes":set(),"missing":0,"negative":0,"zero":0,"minimum":None,"maximum":None,"invalid_dates":0,"date_min":None,"date_max":None,"outliers_iqr_sample":None})
 26                  a['dtypes'].add(str(s.dtype)); a['missing']+=int(s.isna().sum())
 27                  decode_errors+=int(s.astype(str).str.contains('\ufffd',regex=False).sum())
```

Initialize each column's counters, capture observed chunk dtypes and missing values, and count Unicode replacement characters as a decoding-quality signal. Replacement characters are a warning proxy, not proof of the original error.


### Line 28

```text
 28                  if pd.api.types.is_numeric_dtype(s) and not any(t in snake_case(c) for t in ["customer_id","customer_id","phone","password","email","street","zip"]):
```

Limit numeric range/outlier reporting to numeric columns whose names do not match the listed sensitive hints. customer_id is repeated harmlessly in this list; this is a basic name heuristic, not comprehensive classification.


### Line 29–33

```text
 29                      a['negative']+=int((s<0).sum());a['zero']+=int((s==0).sum())
 30                      if s.notna().any():
 31                          lo=float(s.min());hi=float(s.max())
 32                          a['minimum']=lo if a['minimum'] is None else min(lo,a['minimum'])
 33                          a['maximum']=hi if a['maximum'] is None else max(hi,a['maximum'])
```

Count negative/zero values and keep global minimum/maximum. A negative profit can be legitimate; the audit reports it without deleting it.


### Line 34–36

```text
 34                      if a['outliers_iqr_sample'] is None:
 35                          q1,q3=s.quantile([.25,.75]);iqr=q3-q1
 36                          a['outliers_iqr_sample']=int(((s<q1-1.5*iqr)|(s>q3+1.5*iqr)).sum())
```

Compute a 1.5-IQR outlier screen on the first numeric chunk only. This is a cheap descriptive sample, not full-file outlier detection and not a removal rule.


### Line 37–41

```text
 37                  # Date columns only; never log values for names/addresses/identifiers.
 38                  if 'date' in snake_case(c) and not pd.api.types.is_numeric_dtype(s):
 39                      d=pd.to_datetime(s,errors='coerce',format='mixed');a['invalid_dates']+=int((s.notna() & d.isna()).sum())
 40                      if d.notna().any():
 41                          lo=str(d.min());hi=str(d.max());a['date_min']=min(a['date_min'] or lo,lo);a['date_max']=max(a['date_max'] or hi,hi)
```

Try mixed-format parsing only for nonnumeric columns with date in the name; count failed nonmissing dates and preserve observed date range.


### Line 42–45

```text
 42          for c in columns:
 43              a=stats[c];a['dtypes']=sorted(a['dtypes'])
 44              a['unique_values']=con.execute(f"SELECT count(DISTINCT {quote_identifier(c)}) FROM audit").fetchone()[0]
 45          duplicates=con.execute("SELECT (SELECT count(*) FROM audit)-count(*) FROM (SELECT DISTINCT * FROM audit)").fetchone()[0]
```

Convert dtype sets to serializable lists and obtain exact distinct counts and full-row duplicate counts with DuckDB. Identical source rows and duplicate business keys are separate problems.


### Line 46

```text
 46      con.close()
```

Close the audit engine after the temporary-file context exits.


### Line 47–52

```text
 47      report={"filename":path.name,"rows":rows,"columns":len(columns),"column_stats":stats,
 48        "duplicate_rows":duplicates,"encoding":encoding,"replacement_character_count":decode_errors,
 49        "peak_chunk_memory_bytes":peak,"file_size_bytes":path.stat().st_size,
 50        "outlier_method":"1.5 IQR on first 10,000 rows per numeric column; descriptive screen, not removal"}
 51      write_json(Path(report_dir)/(path.stem+"_audit.json"),report)
 52      return report
```

Write a JSON audit with source dimensions, counter statistics, encoding and explicit sampled-outlier methodology; return it for direct inspection.


### Line 53

```text
 53
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 54–58

```text
 54  def validate_m5(con):
 55      for table,cols in {"raw_sales":["id","item_id","dept_id","cat_id","store_id","state_id"],
 56         "calendar":["d","date","wm_yr_wk","snap_CA","snap_TX","snap_WI"],
 57         "prices":["item_id","store_id","wm_yr_wk","sell_price"]}.items():
 58          required_columns([x[0] for x in con.execute(f"DESCRIBE {table}").fetchall()],cols,table)
```

Check the minimum required columns in raw M5 sales, calendar and price tables. Some later-consumed calendar columns are not listed here, so this is a partial schema contract.


### Line 59

```text
 59      require_zero(con,"SELECT count(*) FROM (SELECT item_id,store_id FROM raw_sales GROUP BY ALL HAVING count(*)>1)","Duplicate M5 series")
```

Reject repeated item-store sales series because unpivoting them would double-count daily demand.


### Line 60–61

```text
 60      require_zero(con,"SELECT count(*) FROM (SELECT d FROM calendar GROUP BY d HAVING count(*)>1)","Duplicate calendar day")
 61      require_zero(con,"SELECT count(*) FROM calendar WHERE try_cast(date AS DATE) IS NULL","Invalid M5 dates")
```

Reject duplicate day identifiers and invalid calendar dates to preserve one-to-one day mapping.


### Line 62

```text
 62      require_zero(con,"SELECT count(*) FROM prices WHERE sell_price < 0 OR sell_price IS NULL","Invalid sell prices")
```

Reject negative or missing price rows. Zero prices are allowed by this rule.


### Line 63–66

```text
 63      cols=[c[0] for c in con.execute('DESCRIBE raw_sales').fetchall() if c[0].startswith('d_')]
 64      if not cols: raise ValueError('No M5 day columns')
 65      checks=' OR '.join(f'"{c}" IS NULL OR "{c}" < 0' for c in cols)
 66      require_zero(con,'SELECT count(*) FROM raw_sales WHERE '+checks,'Null or negative raw demand')
```

Discover day columns, reject a file without them, and reject null/negative sales values before unpivoting. A zero means recorded zero sales, not a missing record.


### Line 67–69

```text
 67      require_zero(con,"SELECT count(*) FROM (SELECT date FROM calendar GROUP BY date HAVING count(*)>1)","Duplicate calendar date")
 68      require_zero(con,"SELECT count(*) FROM raw_sales WHERE item_id IS NULL OR store_id IS NULL OR state_id NOT IN ('CA','TX','WI')","Invalid M5 identity/state")
 69      require_zero(con,"SELECT count(*) FROM (SELECT item_id,store_id,wm_yr_wk FROM prices GROUP BY ALL HAVING count(*)>1)","Duplicate weekly price")
```

Require unique calendar dates, valid core identity/state codes and one weekly price per item/store/week. The identity query does not validate every possible null metadata field.


### Line 70

```text
 70
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 71–72

```text
 71  def validate_sales(con):
 72      require_zero(con,"SELECT count(*) FROM sales_long WHERE units_sold IS NULL OR units_sold<0 OR date IS NULL", "Invalid demand/date or missing calendar join")
```

After joins, reject missing dates and null/negative units; a missing calendar match is a source error.


### Line 73

```text
 73      require_zero(con,"SELECT count(*) FROM sales_long WHERE units_sold>0 AND sell_price IS NULL", "Positive demand with missing price; correct source before revenue analysis")
```

Require a price for positive sales so revenue cannot silently be understated. Zero-sales rows can retain a missing price because their constructed revenue is zero.


### Line 74

```text
 74      require_zero(con,"SELECT count(*) FROM (SELECT item_id,store_id,date FROM sales_long GROUP BY ALL HAVING count(*)<>1)","Nonunique daily sales")
```

Enforce one daily row per item/store/date to catch join multiplication.


### Line 75

```text
 75      require_zero(con,"SELECT count(*) FROM (SELECT item_id,store_id,count(*) n,date_diff('day',min(date),max(date))+1 expected FROM sales_long GROUP BY ALL) WHERE n<>expected","Non-contiguous demand history")
```

Compare row count with inclusive date-span length for each series. Combined with unique dates, this detects gaps, which would make row-based lags mean the wrong number of days.


## src/validation/schema_validation.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1–3

```text
  1  def required_columns(columns, required, label):
  2      missing=set(required)-set(columns)
  3      if missing: raise ValueError(f"{label}: missing required columns {sorted(missing)}")
```

Compute required-minus-present column names and fail if any are missing. This converts obscure later attribute errors into a clear source-contract error.


### Line 4–6

```text
  4  def unique_keys(frame, keys):
  5      if frame[keys].isna().any().any() or frame.duplicated(keys).any():
  6          raise ValueError(f"Null or duplicate key: {keys}")
```

Reject null or duplicate composite keys. A business key must identify exactly one row before safe joins and sums are possible.


### Line 7–8

```text
  7  def require_zero(con, query, message):
  8      if con.execute(query).fetchone()[0]: raise ValueError(message)
```

Execute a SQL failure-count query and raise if its first value is nonzero. Callers write each query so zero means the invariant holds.


## src/transformation/build_dimensions.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 2

```text
  2  from src.utils.file_utils import export_frame
```

Import export_frame from src.utils.file_utils to provide reuse src/utils/file_utils.py rather than duplicating that stage’s implementation.


### Line 3

```text
  3
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 4–6

```text
  4  def build_dimensions(con,lines,delivery,out):
  5      queries={
  6      'dim_date':"SELECT DISTINCT cast(date AS DATE) date,cast(strftime(cast(date AS DATE),'%Y%m%d') AS INTEGER) date_key,year(cast(date AS DATE)) AS year,month(cast(date AS DATE)) AS month,quarter(cast(date AS DATE)) AS quarter FROM calendar",
```

Define queries for dimensions, starting with a deduplicated date table carrying numeric date keys and calendar attributes.


### Line 7–11

```text
  7      'dim_product':"SELECT DISTINCT item_id,department_id,category_id FROM sales",
  8      'dim_store':"SELECT DISTINCT store_id,state_id FROM sales",
  9      'dim_state':"SELECT DISTINCT state_id FROM sales",
 10      'dim_category':"SELECT DISTINCT category_id FROM sales",
 11      'dim_department':"SELECT DISTINCT department_id,category_id FROM sales",
```

Extract product, store, state, category and department lookup tables. Facts can then reference a single consistent description of each entity.


### Line 12

```text
 12      'dim_event':"SELECT DISTINCT event_name,event_type FROM (SELECT event_name_1 event_name,event_type_1 event_type FROM calendar UNION SELECT event_name_2,event_type_2 FROM calendar) WHERE event_name IS NOT NULL",
```

Union both event slots and deduplicate named events. An event name is assumed to have a unique type.


### Line 13

```text
 13      'bridge_date_event':"SELECT DISTINCT cast(strftime(cast(date AS DATE),'%Y%m%d') AS INTEGER) date_key,event_name FROM (SELECT date,event_name_1 event_name FROM calendar UNION SELECT date,event_name_2 FROM calendar) WHERE event_name IS NOT NULL",
```

Create a date-event bridge to preserve two events on one day without duplicating sales fact rows.


### Line 14

```text
 14      'fact_sell_price':"SELECT DISTINCT item_id,store_id,wm_yr_wk,sell_price FROM sales WHERE sell_price IS NOT NULL"}
```

Extract weekly prices actually represented in the chosen sales panel; this is not a full export of all raw prices or future price schedules.


### Line 15

```text
 15      dims={name:con.execute(q).df() for name,q in queries.items()}
```

Execute the dimension queries into small Pandas frames; these tables are far smaller than daily sales.


### Line 16–18

```text
 16      dates=pd.date_range(min(pd.to_datetime(dims['dim_date'].date).min(),lines.order_date.min()),max(pd.to_datetime(dims['dim_date'].date).max(),lines.order_date.max()))
 17      dims['dim_date']=pd.DataFrame({'date':dates,'date_key':dates.strftime('%Y%m%d').astype(int),'year':dates.year,'month':dates.month,'quarter':dates.quarter})
 18      dims['dim_order_date']=dims['dim_date'].copy()
```

Build a continuous date range covering both domains and copy it as the DataCo order-date dimension. Separate BI roles allow independent date filtering even when calendar values overlap.


### Line 19

```text
 19      for name,col in [('dim_product_category','category'),('dim_market','market'),('dim_region','region'),('dim_shipping_mode','shipping_mode'),('dim_customer_segment','customer_segment')]: dims[name]=lines[[col]].drop_duplicates()
```

Build DataCo category/market/region/shipping/segment dimensions from cleaned lines, preserving its separate business domain.


### Line 20–22

```text
 20      for name,df in dims.items():
 21          if df.iloc[:,0].duplicated().any() and not name.startswith(('bridge','fact')): raise ValueError('Dimension key not unique: '+name)
 22          export_frame(df,name,out)
```

Check first-column uniqueness for dimensions, skip that single-column rule for bridges/facts with composite keys, and export every table. Composite integrity is also handled downstream.


### Line 23

```text
 23      return dims
```

Return the dimension frames for callers, although the current orchestrator only needs the written outputs.


## src/transformation/transform_dataco.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 2

```text
  2  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws.


### Line 3

```text
  3  from src.validation.schema_validation import required_columns,unique_keys
```

Import required_columns, unique_keys from src.validation.schema_validation to provide reuse src/validation/schema_validation.py rather than duplicating that stage’s implementation.


### Line 4

```text
  4  from src.utils.file_utils import write_json
```

Import write_json from src.utils.file_utils to provide reuse src/utils/file_utils.py rather than duplicating that stage’s implementation.


### Line 5

```text
  5  from pathlib import Path
```

Import Path from pathlib to provide portable filesystem paths; it avoids hard-coding slash separators and supports repository-relative locations.


### Line 6

```text
  6
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 7–10

```text
  7  def transform_dataco(x,cfg,reports):
  8      x=x.copy();required=['order_id','order_item_id','order_date_dateorders']
  9      required_columns(x.columns,required,'DataCo')
 10      unique_keys(x,['order_item_id'])
```

Copy input, require core order/date columns and validate uniqueness of order_item_id. Multiple lines per order are expected; order_id itself should also be explicitly checked for nulls, which this implementation does not do here.


### Line 11

```text
 11      issues={'source_rows':len(x),'repeated_order_ids_expected_for_lines':int(x.order_id.duplicated().sum()),'missing_optional_columns':[]}
```

Record source rows, expected repeated order IDs and missing optional columns for transparency.


### Line 12–14

```text
 12      for c in ['shipping_mode','market','order_region','category_name','customer_segment','product_name','order_status']:
 13          if c not in x: x[c]='Unknown';issues['missing_optional_columns'].append(c)
 14          x[c]=x[c].fillna('Unknown').astype(str).str.strip().str.casefold().replace(cfg.get('category_mappings',{}))
```

Fill absent descriptive categories with Unknown, trim/case-normalize text and apply configured label mappings. Unknown preserves rows; casefold avoids separate groups for superficial capitalization differences.


### Line 15–19

```text
 15      for raw,clean in [('order_date_dateorders','order_date'),('shipping_date_dateorders','shipping_date')]:
 16          if raw in x:
 17              x[clean]=pd.to_datetime(x[raw],format='mixed',errors='coerce').dt.normalize()
 18              issues[clean+'_invalid']=int(x[clean].isna().sum())
 19          else: x[clean]=pd.NaT;issues['missing_optional_columns'].append(raw)
```

Parse order/shipping dates, normalize to midnight and count invalid/missing values. Normalization intentionally removes time-of-day; this project measures delivery in days.


### Line 20–21

```text
 20      if x.order_date.isna().any(): raise ValueError('Invalid DataCo order dates; see source audit')
 21      x['date_key']=x.order_date.dt.strftime('%Y%m%d').astype(int)
```

Reject invalid order dates and derive the date key. A missing shipping date is allowed because source durations may still exist.


### Line 22–25

```text
 22      for raw,clean in [('days_for_shipping_real','actual_shipping_days'),('days_for_shipment_scheduled','scheduled_shipping_days'),
 23                         ('order_item_quantity','quantity'),(cfg['net_sales_source'],'sales'),(cfg['profit_source'],'profit')]:
 24          if raw not in x: x[clean]=np.nan;issues['missing_optional_columns'].append(raw)
 25          else: x[clean]=pd.to_numeric(x[raw],errors='coerce')
```

Convert shipping durations, quantities, configured net sales and configured profit to numbers; unavailable fields become NaN. Configurable source fields avoid assuming that similarly named monetary columns mean the same thing.


### Line 26–27

```text
 26      x['invalid_sales_flag']=x.sales.lt(0)|x.quantity.lt(0)
 27      x['abnormal_profit_flag']=x.profit.abs()>x.sales.abs()*2
```

Flag negative sales/quantities and unusually large absolute profit (>2×absolute sales). Flags preserve evidence; abnormal profit is not automatically excluded. Missing numeric values do not trigger the negative-value flag.


### Line 28

```text
 28      x['delivery_eligible']=x.actual_shipping_days.between(0,cfg['maximum_shipping_days']) & x.scheduled_shipping_days.between(0,cfg['maximum_shipping_days']) & ~x.order_status.isin(['canceled','cancelled','suspected_fraud','suspected fraud'])
```

Define delivery eligibility: both durations within configured bounds and status not cancelled/suspected fraud. Ineligible orders stay in the dataset but cannot be counted as on-time successes.


### Line 29–31

```text
 29      x['delay_days']=(x.actual_shipping_days-x.scheduled_shipping_days).where(x.delivery_eligible)
 30      x['late_order']=x.delay_days.gt(0).astype('Int64').where(x.delivery_eligible)
 31      x['positive_delay_days']=x.delay_days.clip(lower=0)
```

Calculate signed delay, nullable late indicator and positive-only delay. Keeping signed and positive delay separately distinguishes early delivery from average lateness.


### Line 32

```text
 32      x['date_duration_mismatch']=((x.shipping_date-x.order_date).dt.days-x.actual_shipping_days).abs().gt(1) & x.shipping_date.notna()
```

Flag a >1-day mismatch between date-derived and supplied shipping duration. It is reported, not used to override durations or eligibility.


### Line 33–36

```text
 33      if 'late_delivery_risk' in x:
 34          issues['source_late_flag_disagreement']=int((pd.to_numeric(x.late_delivery_risk,errors='coerce').ne(x.late_order)&x.delivery_eligible).sum())
 35      issues.update(invalid_sales_rows=int(x.invalid_sales_flag.sum()),abnormal_profit_rows=int(x.abnormal_profit_flag.sum()),ineligible_delivery_rows=int((~x.delivery_eligible).sum()),date_duration_mismatch=int(x.date_duration_mismatch.sum()))
 36      write_json(Path(reports)/'dataco_quality.json',issues)
```

Compare the supplied late-risk flag with the independently derived outcome and write quality counts. The source label is an audit input, not a predictor.


### Line 37–40

```text
 37      # Group dimensions describing an order must agree; never silently choose an arbitrary category/mode.
 38      cols=['order_date','shipping_mode','market','order_region','customer_segment','actual_shipping_days','scheduled_shipping_days','delivery_eligible','late_order','delay_days','positive_delay_days']
 39      conflicts=x.groupby('order_id')[cols].nunique(dropna=False).gt(1).any(axis=1)
 40      if conflicts.any(): raise ValueError(f'{int(conflicts.sum())} DataCo orders have conflicting shipment attributes; define shipment-level keys before proceeding')
```

Check all shipment-level attributes agree within each order before collapsing lines. Conflicts require a real shipment key; arbitrarily taking the first row would fabricate an order-level outcome.


### Line 41–42

```text
 41      delivery=x.groupby('order_id',as_index=False)[cols+['date_key']].first()
 42      delivery=delivery.rename(columns={'order_region':'region'})
```

After the consistency check, collapse to one row per order and normalize the region name. Pandas groupby drops missing order IDs, making the missing order_id check above a meaningful improvement.


### Line 43–44

```text
 43      linecols=['order_item_id','order_id','order_date','date_key','shipping_mode','market','order_region','category_name','customer_segment','product_name','quantity','sales','profit','invalid_sales_flag','abnormal_profit_flag']
 44      lines=x[linecols].rename(columns={'order_region':'region','category_name':'category'})
```

Select the distinct order-line profit table. Categories/products belong at line grain and can legitimately vary within an order.


### Line 45

```text
 45      lines['profit_margin']=lines.profit.div(lines.sales.replace(0,np.nan))
```

Divide profit by sales with zero sales treated as undefined; a zero denominator does not imply a 0% margin.


### Line 46–47

```text
 46      lines['loss_making_line']=lines.profit.lt(0)
 47      return lines,delivery
```

Flag negative line profit and return the two grains separately. A loss-making line does not necessarily mean the entire order lost money.


## src/transformation/transform_m5.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  from pathlib import Path
```

Import Path from pathlib to provide portable filesystem paths; it avoids hard-coding slash separators and supports repository-relative locations.


### Line 2

```text
  2  from src.utils.file_utils import sql_literal
```

Import sql_literal from src.utils.file_utils to provide reuse src/utils/file_utils.py rather than duplicating that stage’s implementation.


### Line 3

```text
  3  from src.validation.data_quality import validate_sales
```

Import validate_sales from src.validation.data_quality to provide reuse src/validation/data_quality.py rather than duplicating that stage’s implementation.


### Line 4

```text
  4
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 5–7

```text
  5  def transform_m5(con, cfg, mode, output):
  6      con.execute("""CREATE OR REPLACE VIEW unpivoted AS
  7          UNPIVOT raw_sales ON COLUMNS('^d_[0-9]+$') INTO NAME d VALUE units_sold""")
```

Convert d_1, d_2, ... columns into rows named d and units_sold. This long format supports grouping, joins and window features at item-store-day grain.


### Line 8–10

```text
  8      con.execute("""CREATE OR REPLACE VIEW joined AS SELECT
  9          s.id series_id,s.item_id,s.dept_id department_id,s.cat_id category_id,s.store_id,s.state_id,
 10          s.d,cast(c.date AS DATE) date,cast(strftime(cast(c.date AS DATE),'%Y%m%d') AS INTEGER) date_key,
```

Build a joined view with stable product/store identifiers, real date and YYYYMMDD integer key. Natural IDs preserve traceability; the numeric date key supports a dimensional model.


### Line 11

```text
 11          s.units_sold,p.sell_price, CASE WHEN s.units_sold=0 THEN 0 ELSE s.units_sold*p.sell_price END revenue,
```

Calculate units × listed weekly price. Explicitly set revenue to zero for zero units, even if price is missing. This is a revenue proxy, not reconciled net accounting revenue.


### Line 12–14

```text
 12          c.wm_yr_wk,dayofweek(cast(c.date AS DATE)) weekday,month(cast(c.date AS DATE)) AS month,
 13          quarter(cast(c.date AS DATE)) AS quarter,year(cast(c.date AS DATE)) AS year,
 14          c.event_name_1 event_name,c.event_type_1 event_type,c.event_name_2,c.event_type_2,
```

Attach weekly key, date parts and both calendar events. They support seasonality analysis and known-calendar forecasting features.


### Line 15

```text
 15          CASE s.state_id WHEN 'CA' THEN c.snap_CA WHEN 'TX' THEN c.snap_TX WHEN 'WI' THEN c.snap_WI END snap_flag,
```

Select the SNAP flag for the store's state; another state's eligibility would be the wrong explanatory variable.


### Line 16–20

```text
 16          cast(c.event_name_1 IS NOT NULL OR c.event_name_2 IS NOT NULL AS INTEGER) event_flag,
 17          cast(dayofweek(cast(c.date AS DATE)) IN (0,6) AS INTEGER) weekend_flag,
 18          cast(day(cast(c.date AS DATE))=1 AS INTEGER) month_start_flag,
 19          cast(cast(c.date AS DATE)=last_day(cast(c.date AS DATE)) AS INTEGER) month_end_flag,
 20          cast(s.units_sold=0 AS INTEGER) zero_sales_flag
```

Create event/weekend/month-boundary/zero-sales indicators as simple numeric features or descriptors. Not every exported flag is actually included in the model feature list.


### Line 21–22

```text
 21          FROM unpivoted s LEFT JOIN calendar c USING(d)
 22          LEFT JOIN prices p ON s.item_id=p.item_id AND s.store_id=p.store_id AND c.wm_yr_wk=p.wm_yr_wk""")
```

Left-join calendar by d and prices by item/store/calendar week. Left joins retain source sales so subsequent validation can detect unmatched records instead of silently dropping them.


### Line 23–25

```text
 23      # Select the cohort strictly before all validation windows, avoiding selection leakage.
 24      h=max(cfg['forecast_horizon'],cfg['inventory']['simulation_days'])
 25      cutoff=con.execute(f"SELECT max(date)-INTERVAL '{h*cfg['backtest_folds']} days' FROM joined").fetchone()[0]
```

Compute a cutoff before all evaluation windows using the longer of forecast and replay horizons. Sample selection must not use future performance to choose its items.


### Line 26–32

```text
 26      if mode=='sample':
 27          con.execute(f"""CREATE OR REPLACE TABLE cohort AS WITH revenue AS (
 28            SELECT item_id,store_id,sum(revenue) revenue FROM joined
 29            WHERE date<=? AND date>? - INTERVAL '{cfg['selection_days']} days' GROUP BY ALL),
 30            stores AS (SELECT store_id FROM revenue GROUP BY store_id ORDER BY sum(revenue) DESC,store_id LIMIT {int(cfg['sample_stores'])})
 31            SELECT item_id,store_id FROM revenue WHERE store_id IN (SELECT store_id FROM stores)
 32            ORDER BY revenue DESC,item_id,store_id LIMIT {int(cfg['sample_series'])}""",[cutoff,cutoff])
```

For sample mode, total recent revenue before that cutoff, choose leading stores, then choose top item-store pairs across those stores. Stable ID tie-breakers make reruns repeatable. This favors high-revenue pairs and does not guarantee equal numbers per store.


### Line 33

```text
 33      else: con.execute("CREATE OR REPLACE TABLE cohort AS SELECT DISTINCT item_id,store_id FROM raw_sales")
```

For full mode, retain all distinct source item-store pairs. Full transformation does not remove later runtime caps on model training and simulation.


### Line 34–35

```text
 34      con.execute("CREATE OR REPLACE VIEW sales_long AS SELECT j.* FROM joined j JOIN cohort USING(item_id,store_id)")
 35      validate_sales(con)
```

Restrict joined data to the cohort, then validate that daily panel before exporting it.


### Line 36–37

```text
 36      output=Path(output);output.mkdir(parents=True,exist_ok=True)
 37      con.execute(f"COPY (SELECT * FROM sales_long) TO {sql_literal(output)} (FORMAT PARQUET, PARTITION_BY(store_id,year), OVERWRITE_OR_IGNORE true)")
```

Write Parquet partitioned by store/year so future SQL can scan subsets efficiently. The caller clears the output directory first; overwrite-or-ignore alone is not a complete stale-data strategy.


### Line 38

```text
 38      con.execute(f"CREATE OR REPLACE VIEW sales AS SELECT * FROM read_parquet({sql_literal(output/'**/*.parquet')},hive_partitioning=true)")
```

Expose the partitioned files as the canonical sales view, recovering partition keys through Hive-style folder names.


### Line 39

```text
 39      return cutoff
```

Return the cohort cutoff for the run manifest.


## src/forecasting/baselines.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws.


### Line 2

```text
  2  MODELS=['naive','seasonal_7','seasonal_28','moving_average','lightgbm']
```

Define four transparent baselines plus LightGBM so complexity must demonstrate a benefit on held-out dates.


### Line 3–4

```text
  3  def baseline(y, horizon, name):
  4      y=np.asarray(y,dtype=float)
```

Accept a history vector and requested horizon, converting history to numerical values for uniform operations.


### Line 5

```text
  5      if name=='naive': return np.repeat(y[-1],horizon)
```

Naive: repeat the last observed demand every future day. This tests whether a complex model improves on simply persisting the latest level.


### Line 6

```text
  6      if name=='moving_average': return np.repeat(y[-28:].mean(),horizon)
```

Moving average: repeat the last 28-day mean. It smooths daily noise but loses day-of-week variation.


### Line 7–8

```text
  7      period=int(name.split('_')[1])
  8      return np.resize(y[-period:],horizon)
```

For seasonal_7 or seasonal_28, repeat the final 7/28 values until the horizon is filled. np.resize repeats a pattern here; it is not interpolation. Names outside the declared registry are not separately validated.


## src/forecasting/evaluate_models.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws.


### Line 2

```text
  2  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 3

```text
  3  from src.forecasting.baselines import MODELS
```

Import MODELS from src.forecasting.baselines to provide reuse src/forecasting/baselines.py rather than duplicating that stage’s implementation.


### Line 4

```text
  4  from src.forecasting.train_models import train_global,aggregate_statistical
```

Import train_global, aggregate_statistical from src.forecasting.train_models to provide reuse src/forecasting/train_models.py rather than duplicating that stage’s implementation.


### Line 5

```text
  5  from src.forecasting.generate_forecasts import predict_origin
```

Import predict_origin from src.forecasting.generate_forecasts to provide reuse src/forecasting/generate_forecasts.py rather than duplicating that stage’s implementation.


### Line 6

```text
  6  from src.utils.metrics import metrics
```

Import metrics from src.utils.metrics to provide reuse src/utils/metrics.py rather than duplicating that stage’s implementation.


### Line 7

```text
  7
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 8–12

```text
  8  def evaluate_models(con,cfg):
  9      end=pd.Timestamp(con.execute('SELECT max(date) FROM sales').fetchone()[0])
 10      h=max(28,cfg['inventory']['simulation_days']);folds=cfg['backtest_folds']
 11      records=[];comparisons=[]
 12      champion=None
```

Read the last sales date, choose 28/90-day evaluation length, allocate result collections and initialize the eventual winner.


### Line 13–14

```text
 13      for fold in range(1,folds+1):
 14          origin=end-pd.Timedelta(days=(folds-fold+1)*h)
```

Create chronological origins moving toward the end of history. With 3 default folds, calibration, selection and test occupy successive 28-day windows.


### Line 15–18

```text
 15          model,levels,seconds=train_global(con,origin,cfg)
 16          pred=predict_origin(con,origin,h,MODELS,cfg,model,levels)
 17          actual=con.execute('SELECT item_id,store_id,date,units_sold actual_units FROM sales WHERE date>? AND date<=?',[origin,origin+pd.Timedelta(days=h)]).df()
 18          pred=pred.merge(actual,on=['item_id','store_id','date'],validate='many_to_one')
```

Train and forecast at the origin, then attach actuals only for scoring. many_to_one validates unique actual rows while allowing several models per target date; the inner merge does not itself assert complete forecast/actual matching.


### Line 19–20

```text
 19          pred['fold']=fold;pred['split_role']='calibration' if fold<folds-1 else ('selection' if fold==folds-1 else 'test')
 20          pred['error']=pred.forecast_units-pred.actual_units;pred['absolute_error']=pred.error.abs();records.append(pred)
```

Label the fold's role and compute forecast-minus-actual plus absolute error. Earlier folds become calibration when more than three are configured.


### Line 21–24

```text
 21          for name,g in pred.groupby('model'):
 22              comparisons.append(dict(model=name,fold=fold,split_role=g.split_role.iloc[0],origin=origin,
 23               validation_start=origin+pd.Timedelta(days=1),validation_end=origin+pd.Timedelta(days=h),forecast_level='item_store',
 24               training_seconds=seconds if name=='lightgbm' else 0.,**metrics(g.actual_units,g.forecast_units,g.scale)))
```

Calculate per-model item-store scores for that fold and record dates/training time. Baseline training time is set to zero; it does not mean baseline prediction and evaluation take no time.


### Line 25–29

```text
 25          aggregate=actual.groupby('date').actual_units.sum()
 26          for name,p,t in aggregate_statistical(con,origin,h):
 27              comparisons.append(dict(model=name,fold=fold,split_role=pred.split_role.iloc[0],origin=origin,
 28               validation_start=origin+pd.Timedelta(days=1),validation_end=origin+pd.Timedelta(days=h),forecast_level='selected_portfolio_total',
 29               training_seconds=t,**metrics(aggregate,p)))
```

Evaluate ETS/SARIMA against portfolio totals and label the different grain. Aggregation reduces cancellation-sensitive errors and therefore is not an apples-to-apples item-level comparison.


### Line 30–32

```text
 30          if fold==folds-1:
 31              selection=pd.DataFrame(comparisons).query('fold==@fold and forecast_level=="item_store"')
 32              champion=selection.sort_values(['wape','mae','model']).model.iloc[0]
```

Select the winner on the penultimate fold using WAPE, then MAE and model name as deterministic tie-breakers. The final fold never chooses the winner; selecting on one window still gives a noisy decision.


### Line 33–37

```text
 33      backtest=pd.concat(records,ignore_index=True)
 34      # Intervals for held-out test use earlier calibration errors only, before model selection/test outcomes.
 35      calibration=backtest[(backtest.fold<folds-1)&(backtest.model==champion)]
 36      test=backtest[(backtest.fold==folds)&(backtest.model==champion)].copy()
 37      test=add_intervals(test,calibration)
```

Concatenate all predictions; calibrate selected-model test intervals only with earlier calibration folds, excluding both selection and test outcomes from this interval calibration.


### Line 38–40

```text
 38      test['covered_80']=(test.actual_units>=test.lower_80)&(test.actual_units<=test.upper_80)
 39      test['covered_95']=(test.actual_units>=test.lower_95)&(test.actual_units<=test.upper_95)
 40      return backtest,pd.DataFrame(comparisons),test,champion
```

Measure whether observed test units fall inside each band, then return complete evidence. Empirical coverage is assessed, not assumed equal to the nominal 80/95% labels.


### Line 41

```text
 41
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 42–44

```text
 42  def add_intervals(pred,residuals):
 43      pred=pred.copy()
 44      # Signed residual actual-prediction, pooled by forecast day. Approximate, not guaranteed coverage.
```

Copy predictions and describe signed residual correction. The interval is an empirical approximation, not a formally guaranteed or hierarchical calibrated interval.


### Line 45–47

```text
 45      for level in [80,95]:
 46          alpha=(1-level/100)/2
 47          q=residuals.assign(residual=residuals.actual_units-residuals.forecast_units).groupby('horizon').residual.quantile([alpha,1-alpha]).unstack()
```

For each confidence level compute lower/upper quantiles of actual-minus-forecast residuals separately by horizon, pooling series. Different steps can have different uncertainty, but sparse per-horizon samples and pooled item scales limit calibration quality.


### Line 48–50

```text
 48          for label,col in [('lower',0),('upper',1)]:
 49              shift=pred.horizon.map(q.iloc[:,col]).fillna(float((residuals.actual_units-residuals.forecast_units).quantile([alpha,1-alpha][col])))
 50              pred[f'{label}_{level}']=(pred.forecast_units+shift).clip(lower=0)
```

Map each forecast step to residual quantiles, fall back to pooled quantiles when missing, add offsets, and clip impossible negative demand limits.


### Line 51–53

```text
 51          # Ensure point is displayed inside interval while retaining asymmetric residual bounds.
 52          pred[f'lower_{level}']=np.minimum(pred[f'lower_{level}'],pred.forecast_units)
 53          pred[f'upper_{level}']=np.maximum(pred[f'upper_{level}'],pred.forecast_units)
```

Expand limits if necessary so the displayed point forecast lies inside its interval. This is a presentation convention that changes empirical bounds; it does not create a coverage guarantee.


### Line 54

```text
 54      return pred
```

Return forecasts with both bands.


### Line 55

```text
 55
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 56–58

```text
 56  def segment_metrics(test,segments):
 57      x=test.merge(segments[['item_id','store_id','abc_xyz','volume_segment']],on=['item_id','store_id'],validate='many_to_one')
 58      rows=[]
```

Attach pretest segment labels through a validated many-to-one pair join and allocate result rows.


### Line 59–61

```text
 59      for dim in ['state_id','store_id','category_id','department_id','volume_segment','abc_xyz']:
 60          for val,g in x.groupby(dim): rows.append(dict(segment_type=dim,segment=str(val),model=g.model.iloc[0],**metrics(g.actual_units,g.forecast_units,g.scale)))
 61      return pd.DataFrame(rows)
```

Calculate metrics for each state/store/category/department/volume/ABC-XYZ group. These are overlapping analytical views and their rows must not be summed together.


## src/forecasting/feature_engineering.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws.


### Line 2

```text
  2  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 3

```text
  3  LAGS=[1,7,14,28,56]
```

Use yesterday and 1/2/4/8-week lags to capture recent level and repeated weekly behavior. The exact lag set is a chosen starting point, not a proven optimum.


### Line 4

```text
  4  CATEGORICAL=['item_id','store_id','state_id','category_id','department_id','event_type']
```

Declare entity/category/event identifiers as categorical predictors so arbitrary numeric ordering is not imposed on labels.


### Line 5–6

```text
  5  NUMERIC=[f'lag_{x}' for x in LAGS]+[f'rolling_mean_{x}' for x in [7,28,56]]+['rolling_std_7','rolling_std_28','sell_price','price_change_percentage','weekday','week','month','quarter','event_flag','snap_flag','days_since_last_sale']
  6  FEATURES=NUMERIC+CATEGORICAL
```

List the actual model predictors explicitly. This prevents accidental inclusion of target units, revenue or other outcome columns merely because they exist in the feature view.


### Line 7

```text
  7
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 8–10

```text
  8  def create_feature_view(con):
  9      windows=[]
 10      for lag in LAGS: windows.append(f'lag(units_sold,{lag}) OVER w AS lag_{lag}')
```

Generate SQL lag expressions separately within each item-store time series; one store's previous row must not become another's history.


### Line 11–13

```text
 11      for days in [7,28,56]:
 12          frame=f'PARTITION BY item_id,store_id ORDER BY date ROWS BETWEEN {days} PRECEDING AND 1 PRECEDING'
 13          windows.append(f'avg(units_sold) OVER ({frame}) rolling_mean_{days}')
```

Build 7/28/56-day rolling means ending one row before the current target. Excluding the target day is essential to prevent learning its answer.


### Line 14–15

```text
 14          if days in [7,28]:
 15              windows += [f'stddev_samp(units_sold) OVER ({frame}) rolling_std_{days}',f'sum(units_sold) OVER ({frame}) rolling_{days}_day_units',f'sum(revenue) OVER ({frame}) rolling_{days}_day_revenue']
```

Add short/medium-window sample standard deviations and descriptive rolling sums. Rolling units/revenue sums are exported but excluded from FEATURES, so they are not model predictors.


### Line 16–17

```text
 16      con.execute("CREATE OR REPLACE VIEW features AS SELECT *,weekofyear(date) AS week,"+','.join(windows)+""",
 17        sell_price/nullif(lag(sell_price) OVER w,0)-1 price_change_percentage,
```

Create the view and calculate current historical price relative to the previous observed price, guarding a zero denominator. Training sees historical current-day prices; future prediction freezes price, a deliberate availability assumption that can create a train/predict mismatch.


### Line 18–20

```text
 18        date_diff('day',max(CASE WHEN units_sold>0 THEN date END) OVER
 19          (PARTITION BY item_id,store_id ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),date) days_since_last_sale
 20        FROM sales WINDOW w AS (PARTITION BY item_id,store_id ORDER BY date)""")
```

Measure days since the last strictly earlier positive sale. The SQL window ends before the target, preserving the same information boundary as lags.


### Line 21

```text
 21
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 22–24

```text
 22  def past_features(y, prices, date, meta, calendar):
 23      """Only the values supplied in y are used; recursive callers append predictions."""
 24      f=dict(meta);f.update(calendar);n=len(y)
```

Build a single prediction row from only supplied history, metadata and known calendar fields. The caller is responsible for passing no future actual demand.


### Line 25

```text
 25      for k in LAGS: f[f'lag_{k}']=float(y[-k]) if n>=k else np.nan
```

Read lag k as y[-k]; insufficient history becomes NaN, which LightGBM can handle. Negative indexing counts backward from the last available observation.


### Line 26–28

```text
 26      for k in [7,28,56]:
 27          f[f'rolling_mean_{k}']=float(np.mean(y[-k:]))
 28          if k<56: f[f'rolling_std_{k}']=float(np.std(y[-k:],ddof=1)) if n>1 else 0.
```

Recreate rolling averages/stds in Python for recursive prediction. ddof=1 matches sample standard deviation; very short history receives a guarded value.


### Line 29–30

```text
 29      positives=np.flatnonzero(np.asarray(y)>0)
 30      f['days_since_last_sale']=n-int(positives[-1]) if len(positives) else np.nan
```

Find the last positive history element and calculate its age at the next forecast date. If none exists, age is unknown.


### Line 31–32

```text
 31      # Future price is frozen at origin, including every backtest fold.
 32      f['sell_price']=prices[-1];f['price_change_percentage']=0.
```

Use the last known price at every future step and zero future price change. Future price plans are not read by this implementation; price_future_policy in YAML is informational rather than branching logic.


### Line 33–34

```text
 33      f.update(weekday=(date.dayofweek+1)%7,week=int(date.isocalendar().week),month=date.month,quarter=date.quarter)
 34      return f
```

Match DuckDB's Sunday-zero weekday encoding, use ISO week/month/quarter, and return the row. Consistent encodings prevent training/prediction discrepancies.


### Line 35

```text
 35
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 36–38

```text
 36  def encode(frame, levels=None):
 37      x=frame[FEATURES].copy()
 38      if levels is None: levels={c:sorted(frame[c].fillna('Unknown').astype(str).unique()) for c in CATEGORICAL}
```

Select only FEATURES and learn each category vocabulary on the training frame when none is supplied. Evaluation/future rows reuse that vocabulary.


### Line 39

```text
 39      for c in CATEGORICAL: x[c]=pd.Categorical(x[c].fillna('Unknown').astype(str),categories=levels[c])
```

Convert labels to matching Pandas categorical levels. An unseen label becomes missing instead of receiving an arbitrary new code inconsistent with training.


### Line 40–41

```text
 40      for c in NUMERIC: x[c]=pd.to_numeric(x[c],errors='coerce')
 41      return x,levels
```

Coerce numeric fields and return both feature matrix and vocabulary for consistent later prediction.


## src/forecasting/generate_forecasts.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws.


### Line 2

```text
  2  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 3

```text
  3  from src.forecasting.feature_engineering import past_features,encode
```

Import past_features, encode from src.forecasting.feature_engineering to provide reuse src/forecasting/feature_engineering.py rather than duplicating that stage’s implementation.


### Line 4

```text
  4  from src.forecasting.baselines import baseline
```

Import baseline from src.forecasting.baselines to provide reuse src/forecasting/baselines.py rather than duplicating that stage’s implementation.


### Line 5

```text
  5  from src.utils.metrics import rmsse_scale
```

Import rmsse_scale from src.utils.metrics to provide reuse src/utils/metrics.py rather than duplicating that stage’s implementation.


### Line 6

```text
  6
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 7–9

```text
  7  def predict_origin(con,origin,horizon,names,cfg,model=None,levels=None):
  8      origin=pd.Timestamp(origin)
  9      keys=con.execute('SELECT DISTINCT item_id,store_id FROM sales ORDER BY item_id,store_id').df()
```

Normalize the forecast origin and get a stable list of item-store identities. This dataset assumes the panel's identities are known; it is not a cold-start product-launch model.


### Line 10–12

```text
 10      cal=con.execute('SELECT * FROM calendar WHERE cast(date AS DATE)>? AND cast(date AS DATE)<=?',[origin,origin+pd.Timedelta(days=horizon)]).df()
 11      cal['date']=pd.to_datetime(cal.date);cal=cal.set_index('date')
 12      if len(cal)!=horizon: raise ValueError('Calendar must cover every forecast date; add an explicit known-future calendar')
```

Load exactly the next horizon days of known calendar information and fail if coverage is incomplete. Future calendar dates/events are permissible inputs; future observed sales are not.


### Line 13–17

```text
 13      rows=[]
 14      for start in range(0,len(keys),cfg['prediction_batch_series']):
 15          batch=keys.iloc[start:start+cfg['prediction_batch_series']];con.register('batch_keys',batch)
 16          history=con.execute('SELECT s.* FROM sales s JOIN batch_keys USING(item_id,store_id) WHERE date<=? ORDER BY item_id,store_id,date',[origin]).df()
 17          con.unregister('batch_keys')
```

Process a bounded number of series per batch, join their keys into historical sales only through the origin, and unregister the temporary key frame afterward.


### Line 18–23

```text
 18          states=[]
 19          for (item,store),g in history.groupby(['item_id','store_id'],sort=True):
 20              meta=g.iloc[-1].to_dict();y=g.units_sold.to_numpy(float);prices=g.sell_price.dropna().to_list()
 21              if not prices: raise ValueError(f'No known price for {item}/{store}')
 22              meta['scale']=rmsse_scale(y)
 23              states.append((item,store,meta,y.tolist(),prices))
```

For each series retain its latest metadata, past units and known prices; reject completely unknown price, calculate training-only RMSSE scale, and store mutable demand history for recursion. Only the last known nonnull price is later used.


### Line 24–27

```text
 24              for name in names:
 25                  if name=='lightgbm': continue
 26                  for h,pred in enumerate(baseline(y,horizon,name),1):
 27                      rows.append(record(meta,item,store,origin,h,name,pred))
```

Generate all requested baseline forecasts directly from observed history and record each future day with its model/origin metadata.


### Line 28–30

```text
 28          if 'lightgbm' in names:
 29              for h in range(1,horizon+1):
 30                  date=origin+pd.Timedelta(days=h);c=cal.loc[date];features=[]
```

For LightGBM advance one forecast day at a time. Later-day features depend on earlier predictions, so this loop cannot be replaced by feeding actual held-out targets.


### Line 31–34

```text
 31                  for item,store,meta,y,prices in states:
 32                      known={'event_flag':int(pd.notna(c.get('event_name_1')) or pd.notna(c.get('event_name_2'))),
 33                       'event_type':c.get('event_type_1'),'snap_flag':c['snap_'+meta['state_id']]}
 34                      features.append(past_features(y,prices,date,meta,known))
```

Combine known event/SNAP calendar fields with the series' currently available history. State-specific SNAP uses the relevant state's calendar column.


### Line 35

```text
 35                  x,_=encode(pd.DataFrame(features),levels);preds=np.maximum(0,model.predict(x))
```

Encode with the original training category levels, predict the whole batch for this date, and clip negative numerical results to zero.


### Line 36–38

```text
 36                  for state,pred in zip(states,preds):
 37                      item,store,meta,y,prices=state;y.append(float(pred))
 38                      rows.append(record(meta,item,store,origin,h,'lightgbm',pred))
```

Append predicted demand to each series history, then record the forecast. This is recursive multi-step forecasting; errors can propagate and positive fractional predictions can make days-since-last-sale less informative at longer horizons.


### Line 39

```text
 39      return pd.DataFrame(rows)
```

Combine records into one forecast frame. The row list ultimately remains in memory, so batch size alone does not bound total output memory.


### Line 40

```text
 40
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 41–45

```text
 41  def record(meta,item,store,origin,h,name,pred):
 42      date=origin+pd.Timedelta(days=h)
 43      return dict(item_id=item,store_id=store,state_id=meta['state_id'],category_id=meta['category_id'],
 44       department_id=meta['department_id'],origin=origin,date=date,date_key=int(date.strftime('%Y%m%d')),
 45       horizon=h,model=name,forecast_units=float(pred),scale=meta['scale'])
```

Attach pair identity, origin, target date/key, horizon, model, units and training scale to each record. These fields prevent ambiguous joins and support reproducible evaluation.


## src/forecasting/train_models.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import time
```

Import time from time to provide elapsed-time measurement with a monotonic performance counter.


### Line 2

```text
  2  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling. The imported name(s) pandas are not referenced elsewhere in this module’s executable syntax; they are cleanup opportunities rather than needed logic here.


### Line 3

```text
  3  from lightgbm import LGBMRegressor
```

Import LGBMRegressor from lightgbm to provide gradient-boosted tree estimators for demand regression or optional delivery classification.


### Line 4

```text
  4  from src.forecasting.feature_engineering import encode
```

Import encode from src.forecasting.feature_engineering to provide reuse src/forecasting/feature_engineering.py rather than duplicating that stage’s implementation.


### Line 5

```text
  5
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 6–7

```text
  6  def train_global(con,origin,cfg):
  7      start=time.perf_counter()
```

Train a global model at a specified information cutoff and time the training step for comparison.


### Line 8–11

```text
  8      # Deterministic row cap permits bounded training memory even for full M5.
  9      train=con.execute(f"""SELECT * FROM features WHERE date<=? AND
 10        date>? - INTERVAL '{cfg['training_days']} days' AND lag_56 IS NOT NULL
 11        ORDER BY hash(item_id,store_id,date,{int(cfg['seed'])}) LIMIT {int(cfg['max_training_rows'])}""",[origin,origin]).df()
```

Select at most the configured trailing history and row count, require lag_56, and order by a seeded hash for deterministic downsampling. All selected rows precede the origin; it is not a random train/test split. The cap bounds the resulting frame but SQL still scans/sorts candidates.


### Line 12–13

```text
 12      if train.empty: raise ValueError('Not enough training history for lag_56')
 13      x,levels=encode(train)
```

Reject no-data training and encode predictors/category levels from this training subset alone.


### Line 14–15

```text
 14      model=LGBMRegressor(n_estimators=120,num_leaves=31,learning_rate=.05,objective='poisson',
 15          random_state=cfg['seed'],n_jobs=cfg['threads'],deterministic=True,force_col_wise=True,verbosity=-1)
```

Fit 120 boosted trees with up to 31 leaves, learning rate .05 and Poisson objective for nonnegative count-like demand. Seed/thread/determinism flags support reproducibility. These are fixed defaults, not the output of hyperparameter tuning; the Poisson objective does not prove sales follow a Poisson distribution.


### Line 16–17

```text
 16      model.fit(x,train.units_sold)
 17      return model,levels,time.perf_counter()-start
```

Learn against units_sold and return fitted model, vocabulary and elapsed time. The model is used in memory and is not serialized as a reusable deployment artifact.


### Line 18

```text
 18
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 19–22

```text
 19  def aggregate_statistical(con,origin,horizon):
 20      from statsmodels.tsa.holtwinters import ExponentialSmoothing
 21      from statsmodels.tsa.statespace.sarimax import SARIMAX
 22      y=con.execute('SELECT date,sum(units_sold) y FROM sales WHERE date<=? GROUP BY date ORDER BY date',[origin]).df().set_index('date').y.asfreq('D')
```

Aggregate the selected portfolio to daily total demand before fitting classical time-series diagnostics. This reduces fitting cost but changes the forecast grain.


### Line 23–25

```text
 23      result=[]
 24      for name,factory in [('ets',lambda:ExponentialSmoothing(y,trend='add',seasonal='add',seasonal_periods=7,initialization_method='estimated').fit()),
 25                           ('sarima',lambda:SARIMAX(y,order=(1,0,0),seasonal_order=(1,0,0,7),enforce_stationarity=False).fit(disp=False,maxiter=100))]:
```

Define additive weekly ETS and an AR(1) plus seasonal AR(1) SARIMA specification. They illustrate different temporal models; the orders are fixed and not searched for optimal fit.


### Line 26–28

```text
 26          t=time.perf_counter();fit=factory()
 27          result.append((name,fit.forecast(horizon).clip(lower=0).to_numpy(),time.perf_counter()-t))
 28      return result
```

Fit, forecast, clip negative aggregate units and record elapsed time. Their scores are labeled portfolio-total and cannot directly compete with item-store replenishment forecasts.


## src/inventory/calculate_inventory_policy.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import math
```

Import math from math to provide scalar square roots and upward quantity rounding.


### Line 2

```text
  2  from statistics import NormalDist
```

Import NormalDist from statistics to provide the normal-distribution quantile/CDF used by the inventory approximation.


### Line 3

```text
  3  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws.


### Line 4

```text
  4  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 5

```text
  5
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 6–8

```text
  6  def safety_stock(mean,sd,lead,lead_sd,service):
  7      if not 0<service<1: raise ValueError('Service level must be in (0,1)')
  8      if min(mean,sd,lead,lead_sd)<0: raise ValueError('Negative demand/lead parameter')
```

Define safety stock and reject invalid service probabilities or negative inputs. Nonfinite values and all practical distribution constraints are not exhaustively checked by this helper.


### Line 9

```text
  9      return NormalDist().inv_cdf(service)*math.sqrt(lead*sd**2+mean**2*lead_sd**2)
```

Calculate z(service) × sqrt(L×sd² + mean²×lead_sd²). The two terms approximate demand uncertainty during lead time and demand exposure to uncertain lead time. It assumes an appropriate normal approximation and independence; correlated or intermittent demand can violate it.


### Line 10–12

```text
 10  def eoq(annual_demand,ordering_cost,annual_holding_per_unit):
 11      if min(annual_demand,ordering_cost)<0 or annual_holding_per_unit<=0: raise ValueError('Invalid EOQ inputs')
 12      return math.sqrt(2*annual_demand*ordering_cost/annual_holding_per_unit)
```

Calculate EOQ = sqrt(2×annual demand×fixed order cost / annual holding cost per unit), rejecting invalid denominators. Classical EOQ assumes a simplified stable-demand cost balance; it is a heuristic inside this more complicated simulation.


### Line 13–15

```text
 13  def round_order(q,moq,pack):
 14      if pack<=0 or moq<0: raise ValueError('Invalid lot constraints')
 15      return math.ceil(max(q,moq)/pack)*pack if q>0 else 0
```

For positive replenishment need, apply minimum order quantity then round upward to a whole case pack. Zero/negative need stays zero so an MOQ does not force an unnecessary order.


### Line 16

```text
 16
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 17–20

```text
 17  def policies(history,forecasts,assumptions,errors,service_levels,as_of):
 18      means=forecasts.groupby(['item_id','store_id']).forecast_units.mean().rename('forecast_daily_demand')
 19      err=errors.groupby(['item_id','store_id']).error.std().rename('forecast_error_std')
 20      x=history.merge(assumptions,on=['item_id','store_id'],validate='one_to_one').merge(means,on=['item_id','store_id'],validate='one_to_one').merge(err,on=['item_id','store_id'],how='left',validate='one_to_one')
```

Calculate pair-level mean forecast and historical forecast-error standard deviation, then combine history, assumptions and errors with one-to-one validation. Inner joins can omit missing matches; a completeness assertion would strengthen this.


### Line 21–26

```text
 21      rows=[]
 22      for r in x.to_dict('records'):
 23          for field in ['estimated_unit_cost','annual_holding_cost_rate','case_pack_size','review_period_days','average_lead_time_days']:
 24              if pd.isna(r[field]) or r[field]<=0: raise ValueError('Invalid assumption: '+field)
 25          for field in ['initial_inventory','lead_time_standard_deviation','ordering_cost_per_order','lost_sale_penalty','minimum_order_quantity']:
 26              if pd.isna(r[field]) or r[field]<0: raise ValueError('Invalid assumption: '+field)
```

Allocate outputs and validate positive/nonnegative assumption groups. This prevents impossible costs, cadence and lot sizes from entering policy formulas.


### Line 27–28

```text
 27          for level in service_levels:
 28              p=dict(r);p['target_service_level']=level;p['as_of_date']=pd.Timestamp(as_of)
```

Create a separate policy row for every requested service level and as-of date. Those rows are alternative decisions, not additive inventory holdings.


### Line 29–30

```text
 29              mean=r['forecast_daily_demand'];sd=r['forecast_error_std']
 30              if pd.isna(sd): sd=r['demand_std']
```

Use mean predicted daily demand and residual standard deviation; fall back to observed demand standard deviation if errors are missing. The fallback measures a different kind of uncertainty and should be interpreted accordingly.


### Line 31–32

```text
 31              L=r['average_lead_time_days'];R=r['review_period_days'];ls=r['lead_time_standard_deviation']
 32              ss=safety_stock(mean,sd,L,ls,level);protection_ss=safety_stock(mean,sd,L+R,ls,level)
```

Distinguish lead time L from periodic review interval R. Stock must cover L+R until the next review's replenishment can arrive, so periodic protection uses a longer window than simple reorder-point safety stock.


### Line 33–35

```text
 33              p.update(safety_stock=ss,expected_lead_time_demand=mean*L,reorder_point=mean*L+ss,
 34                protection_safety_stock=protection_ss,order_up_to_level=mean*(L+R)+protection_ss,
 35                eoq=eoq(mean*365,r['ordering_cost_per_order'],r['estimated_unit_cost']*r['annual_holding_cost_rate']),
```

Store lead-time safety stock/reorder point, periodic order-up-to target and EOQ. Multiply daily forecast by 365 for annual EOQ demand; this assumes current expected demand represents the year.


### Line 36–37

```text
 36                days_of_supply=r['initial_inventory']/mean if mean else np.nan,
 37                inventory_value=r['initial_inventory']*r['estimated_unit_cost'],demand_uncertainty_std=sd)
```

Calculate starting days of supply, inventory investment and the uncertainty used. Zero forecast demand yields undefined days of supply rather than an arbitrary finite number.


### Line 38–40

```text
 38              # Normal lead-time-demand approximation; no incoming POs in assumed starting inventory.
 39              sigma=math.sqrt(L*sd**2+mean**2*ls**2)
 40              p['stockout_probability']=1-NormalDist(mean*L,sigma).cdf(r['initial_inventory']) if sigma>0 else float(r['initial_inventory']<mean*L)
```

Approximate the chance that lead-time demand exceeds assumed starting inventory, with a deterministic branch when variance is zero. It excludes initial incoming purchase orders and is not a calibrated real stockout probability.


### Line 41

```text
 41              p['recommended_order_quantity']=round_order(max(p['eoq'],p['order_up_to_level']-r['initial_inventory']),r['minimum_order_quantity'],r['case_pack_size']) if r['initial_inventory']<p['order_up_to_level'] else 0
```

If below the protection target, order at least EOQ or the gap, whichever is larger, subject to lot constraints. This is a combined heuristic and can overshoot the target; it is not a constrained optimization solver.


### Line 42–44

```text
 42              p['excess_units']=max(0,r['initial_inventory']-p['order_up_to_level']);p['excess_value']=p['excess_units']*r['estimated_unit_cost']
 43              rows.append(p)
 44      return pd.DataFrame(rows)
```

Value any stock above the protection target, collect policy rows and return a frame. Excess is relative to the modeled target, not confirmed obsolete stock.


## src/inventory/create_assumptions.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws.


### Line 2

```text
  2  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 3

```text
  3
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 4–5

```text
  4  def create_assumptions(history,cfg):
  5      a=cfg['inventory'];rng=np.random.default_rng(cfg['seed']);rows=[]
```

Read inventory defaults and create a seeded random generator. A fixed seed makes an illustrative scenario reproducible; it does not make its assumptions true.


### Line 6

```text
  6      for r in history.sort_values(['item_id','store_id']).itertuples():
```

Iterate in stable item-store order so each pair receives the same random draw when the input set/order is unchanged.


### Line 7

```text
  7          rows.append(dict(item_id=r.item_id,store_id=r.store_id,supplier_id='SIM_'+r.category_id,
```

Attach pair identity and a clearly synthetic supplier label derived from category. These are not verified suppliers.


### Line 8

```text
  8            average_lead_time_days=int(rng.integers(*a['lead_time_days_range'],endpoint=True)),
```

Draw integer mean lead time inclusively from the configured range. This varies hypothetical supplier conditions across pairs.


### Line 9–10

```text
  9            lead_time_standard_deviation=a['lead_time_std_days'],ordering_cost_per_order=a['ordering_cost'],
 10            annual_holding_cost_rate=a['holding_rate'],estimated_unit_cost=max(.01,r.last_price*a['cost_to_price_ratio']),
```

Assign lead-time uncertainty, fixed ordering cost, annual carrying rate and estimated unit cost as a fraction of price. The small cost floor prevents invalid EOQ division but is an assumption.


### Line 11

```text
 11            target_service_level=a['default_service_level'],initial_inventory=int(np.ceil(r.average_daily_demand*a['initial_days_supply'])),
```

Set default service probability and opening units as recent daily demand × assumed days of supply, rounded up. Opening stock is not measured inventory.


### Line 12–13

```text
 12            review_period_days=a['review_period_days'],lost_sale_penalty=r.last_price*a['lost_sale_penalty_to_price'],
 13            minimum_order_quantity=a['minimum_order_quantity'],case_pack_size=a['case_pack_size'],
```

Attach review cadence, penalty per lost unit and procurement lot constraints. These determine the cost/service trade-off and whether suggested quantities can be ordered.


### Line 14–15

```text
 14            assumption_type='simulated_not_walmart',seed=cfg['seed']))
 15      return pd.DataFrame(rows)
```

Explicitly label inputs simulated_not_walmart and retain the seed, then return the assumption table.


## src/inventory/inventory_simulation.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import math
```

Import math from math to provide scalar square roots and upward quantity rounding.


### Line 2

```text
  2  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws.


### Line 3

```text
  3  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 4

```text
  4  from src.inventory.calculate_inventory_policy import round_order
```

Import round_order from src.inventory.calculate_inventory_policy to provide reuse src/inventory/calculate_inventory_policy.py rather than duplicating that stage’s implementation.


### Line 5

```text
  5
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 6–9

```text
  6  def simulate_series(actual,forecast,dates,p,policy,seed,run_id,baseline_days_cover=14,scenario='base'):
  7      """Lost-sales simulation. Receive -> demand -> review/order; arrivals >= tomorrow.
  8      A common random lead-time draw is indexed by calendar day across policies.
  9      """
```

Define a daily lost-sales simulator with an explicit sequence: receive, serve demand, review/order. Orders cannot arrive immediately. Calendar-day-indexed common random draws support fair paired comparisons.


### Line 10–11

```text
 10      rng=np.random.default_rng(seed)
 11      lead_times=np.maximum(1,np.rint(rng.normal(p['average_lead_time_days'],p['lead_time_standard_deviation'],len(actual))).astype(int))
```

Generate normally distributed lead-time draws, round to days and floor at one. Rounding/flooring changes the realized distribution; normal lead times are a convenience, not empirically fitted supplier behavior.


### Line 12

```text
 12      on_hand=float(p['initial_inventory']);pipeline=[];rows=[];cycle_loss=False;cycle_started=False
```

Initialize on-hand stock, future receipts, output records and replenishment-cycle tracking. There are no opening purchase orders/backorders.


### Line 13–14

```text
 13      for day,(demand,pred,date) in enumerate(zip(actual,forecast,dates)):
 14          opening=on_hand;arrivals=sum(q for t,q in pipeline if t==day)
```

Walk through demand, forecast and dates together; record stock before today's receipts and sum purchase orders due today. zip would silently truncate unequal input lengths, so caller alignment matters.


### Line 15–17

```text
 15          # Complete an actual replenishment cycle only upon a receipt; do not count unfinished cycles.
 16          completed=int(arrivals>0 and cycle_started);successful=int(completed and not cycle_loss)
 17          if arrivals>0: cycle_loss=False;cycle_started=True
```

Count a completed cycle only at a replenishment receipt after an earlier receipt started a cycle. Exclude opening and unfinished cycles. With short simulations, few or no completed cycles can make cycle-service estimates unstable/undefined.


### Line 18

```text
 18          pipeline=[(t,q) for t,q in pipeline if t>day];on_hand+=arrivals
```

Remove received orders from the pipeline and add arrivals to available stock before demand occurs.


### Line 19

```text
 19          fulfilled=min(on_hand,float(demand));lost=float(demand)-fulfilled;on_hand-=fulfilled
```

Fulfill only what is in stock, mark the remainder lost and reduce stock. Lost demand is not backordered into tomorrow.


### Line 20

```text
 20          cycle_loss=cycle_loss or lost>0;in_transit=sum(q for _,q in pipeline);position=on_hand+in_transit;order=0
```

Track any shortage during the current replenishment cycle and compute inventory position = on-hand + outstanding orders. Including on-order stock prevents repeated overordering.


### Line 21

```text
 21          if day % int(p['review_period_days'])==0:
```

Review on day zero and every configured review period. Between review days no new order is placed.


### Line 22–24

```text
 22              if policy=='baseline':
 23                  target=p['average_daily_demand']*baseline_days_cover
 24                  order=round_order(target-position,p['minimum_order_quantity'],p['case_pack_size'])
```

Baseline target equals historical mean demand × fixed days cover; order the gap to inventory position with the same MOQ/case rounding as the alternative policy.


### Line 25–29

```text
 25              else:
 26                  # Rolling future forecast protection window, padded with terminal daily forecast.
 27                  protection=int(math.ceil(p['average_lead_time_days']+p['review_period_days']))
 28                  future=np.asarray(forecast[day+1:day+1+protection],float)
 29                  target=float(future.sum()+(protection-len(future))*forecast[-1])+p['protection_safety_stock']
```

The forecast-driven target covers future L+R days plus protection safety stock. Use remaining daily forecasts and pad beyond the available horizon with the final forecast; this end-of-horizon extrapolation is a practical assumption.


### Line 30–32

```text
 30                  if position<target:
 31                      order=round_order(max(p['eoq'],target-position),p['minimum_order_quantity'],p['case_pack_size'])
 32              if order: pipeline.append((day+int(lead_times[day]),order))
```

If below target, place the larger of EOQ and target gap, rounded for purchasing constraints, with receipt on today's seeded lead-time draw. Policies use the same draw on the same day, though they may order on different days.


### Line 33–34

```text
 33          holding=on_hand*p['estimated_unit_cost']*p['annual_holding_cost_rate']/365
 34          ordering=p['ordering_cost_per_order'] if order else 0.;lost_cost=lost*p['lost_sale_penalty']
```

Charge end-of-day stock holding cost, fixed cost for a placed order and lost-unit penalty. Purchase cash flow, transport capacity, expiry and financing detail are not modeled.


### Line 35–41

```text
 35          rows.append(dict(item_id=p['item_id'],store_id=p['store_id'],date=date,policy=policy,scenario=scenario,
 36           run_id=run_id,target_service_level=p['target_service_level'],opening_inventory=opening,arrivals=arrivals,
 37           forecast_demand=float(pred),actual_demand=float(demand),fulfilled_units=fulfilled,lost_sales_units=lost,
 38           order_quantity=order,in_transit_units=sum(q for _,q in pipeline),closing_inventory=on_hand,
 39           stockout_event=int(lost>0),holding_cost=holding,ordering_cost=ordering,lost_sale_cost=lost_cost,
 40           total_inventory_cost=holding+ordering+lost_cost,lost_sales_value=lost*p['last_price'],
 41           estimated_unit_cost=p['estimated_unit_cost'],completed_cycles=completed,successful_cycles=successful))
```

Write identity, scenario/run/service dimensions, demand, receipts, orders, stock balances, costs and cycle counts for each simulated day. Keeping this ledger makes conservation checks and explanations possible. Lost-sales value uses price and differs from the penalty used in total cost.


### Line 42

```text
 42      return pd.DataFrame(rows)
```

Return the complete daily ledger for one pair/policy/run.


### Line 43

```text
 43
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 44–48

```text
 44  def simulate(test,policies,cfg,scenario='base'):
 45      rows=[]
 46      for idx,((item,store),g) in enumerate(test.groupby(['item_id','store_id'],sort=True)):
 47          g=g.sort_values('date')
 48          for p in policies[(policies.item_id==item)&(policies.store_id==store)].to_dict('records'):
```

Iterate pairs in stable order, sort each demand path chronologically and select that pair's alternative service policies.


### Line 49–52

```text
 49              for run in range(cfg['inventory']['monte_carlo_runs']):
 50                  for policy in ['baseline','optimized']:
 51                      rows.append(simulate_series(g.actual_units.to_numpy(),g.forecast_units.to_numpy(),g.date,p,policy,
 52                       cfg['seed']+idx*10000+run,run,cfg['inventory']['baseline_days_cover'],scenario))
```

Run each policy repeatedly with seeds based on pair index and run number, deliberately excluding policy/service from the seed. Repetitions randomize lead times only; historical demand is the same path in every run. Changing the selected pair set can change index-based seeds.


### Line 53–54

```text
 53      daily=pd.concat(rows,ignore_index=True)
 54      return daily,summarize(daily)
```

Concatenate all ledgers and produce summary KPIs. The complete output is materialized in memory.


### Line 55

```text
 55
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 56–62

```text
 56  def summarize(daily):
 57      keys=['item_id','store_id','policy','scenario','target_service_level','run_id']
 58      k=daily.groupby(keys).agg(actual_demand=('actual_demand','sum'),fulfilled_units=('fulfilled_units','sum'),lost_sales_units=('lost_sales_units','sum'),
 59        lost_sales_value=('lost_sales_value','sum'),average_inventory=('closing_inventory','mean'),maximum_inventory=('closing_inventory','max'),
 60        stockout_days=('stockout_event','sum'),holding_cost=('holding_cost','sum'),ordering_cost=('ordering_cost','sum'),
 61        lost_sale_cost=('lost_sale_cost','sum'),total_inventory_cost=('total_inventory_cost','sum'),
 62        completed_cycles=('completed_cycles','sum'),successful_cycles=('successful_cycles','sum'),days=('date','size')).reset_index()
```

Aggregate at pair + policy + scenario + service + run grain. Sum quantities/costs/events, average/max inventory, and retain observed days/cycles for correct denominators.


### Line 63

```text
 63      k['fill_rate']=k.fulfilled_units.div(k.actual_demand.replace(0,np.nan))
```

Fill rate = fulfilled units / requested units; zero demand is undefined. It is unit-weighted and is different from probability of a no-shortage cycle.


### Line 64

```text
 64      k['cycle_service_level']=k.successful_cycles.div(k.completed_cycles.replace(0,np.nan))
```

Cycle service = successful completed cycles / completed cycles; no completed cycles gives undefined, not 100%.


### Line 65

```text
 65      k['inventory_turnover']=k.fulfilled_units.div(k.average_inventory.replace(0,np.nan))*365/k.days
```

Annualize fulfilled units divided by average units in stock. This is a unit turnover proxy over a short horizon, not audited financial inventory turnover.


### Line 66–68

```text
 66      join=['item_id','store_id','scenario','target_service_level','run_id']
 67      b=k[k.policy=='baseline'][join+['total_inventory_cost','lost_sales_value']].rename(columns={'total_inventory_cost':'baseline_cost','lost_sales_value':'baseline_lost_sales_value'})
 68      k=k.merge(b,on=join,validate='many_to_one')
```

Join each scenario to its matching baseline at identical pair/service/run. validate='many_to_one' prevents baseline duplicates multiplying outcomes.


### Line 69–71

```text
 69      k['estimated_cost_reduction']=k.baseline_cost-k.total_inventory_cost
 70      k['estimated_revenue_protected']=k.baseline_lost_sales_value-k.lost_sales_value
 71      return k
```

Calculate baseline-minus-alternative cost and lost-sales-value differences. Negative savings are retained. The baseline compared with itself yields zero, then the KPI table is returned.


## src/inventory/sensitivity_analysis.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 2

```text
  2  from src.inventory.calculate_inventory_policy import policies
```

Import policies from src.inventory.calculate_inventory_policy to provide reuse src/inventory/calculate_inventory_policy.py rather than duplicating that stage’s implementation.


### Line 3

```text
  3  from src.inventory.inventory_simulation import simulate
```

Import simulate from src.inventory.inventory_simulation to provide reuse src/inventory/inventory_simulation.py rather than duplicating that stage’s implementation.


### Line 4

```text
  4
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 5–8

```text
  5  def sensitivity(history,forecasts,assumptions,errors,test,cfg,origin):
  6      # One-factor-at-a-time scenarios; same random streams support paired comparisons.
  7      keys=history.sort_values(['item_id','store_id']).head(cfg['inventory']['sensitivity_series_limit'])[['item_id','store_id']]
  8      history=history.merge(keys);forecasts=forecasts.merge(keys);assumptions=assumptions.merge(keys);errors=errors.merge(keys);test=test.merge(keys)
```

Limit sensitivity to a deterministic subset and align history, forecasts, assumptions, residuals and actuals to it. Its scope can differ from the base simulation, so raw totals are not automatically comparable.


### Line 9–10

```text
  9      rows=[]
 10      cases=[('base',None,1)]+[(name+'_'+str(factor),name,factor) for name in ['average_lead_time_days','lead_time_standard_deviation','annual_holding_cost_rate','ordering_cost_per_order','forecast_error','lost_sale_penalty'] for factor in [.5,1.5]]
```

Define base plus 0.5×/1.5× scenarios for six uncertainty/cost factors. One-factor-at-a-time analysis is interpretable but misses interactions between simultaneous changes.


### Line 11–14

```text
 11      for name,col,factor in cases:
 12          a=assumptions.copy();e=errors.copy()
 13          if col=='forecast_error': e['error']*=factor
 14          elif col: a[col]*=factor
```

Copy inputs for each scenario to avoid contaminating the next; multiply residual errors for forecast-error sensitivity, or the relevant assumption otherwise. Error scaling changes policy buffers, not the actual historical demand path or the point forecasts.


### Line 15–17

```text
 15          p=policies(history,forecasts,a,e,cfg['inventory']['service_levels'],origin)
 16          _,k=simulate(test,p,cfg,scenario=name);k['sensitivity_factor']=col or 'none';k['multiplier']=factor;rows.append(k)
 17      return pd.concat(rows,ignore_index=True)
```

Recompute policies, replay with matching random seeds, label factor/multiplier and combine scenario KPIs. These are sensitivity results, not probabilities assigned to future states.


## src/operations/delivery_analysis.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 2

```text
  2
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 3–7

```text
  3  def delivery_summary(delivery):
  4      rows=[]
  5      for dim in ['shipping_mode','market','region','customer_segment']:
  6          for val,g in delivery.groupby(dim):
  7              eligible=g[g.delivery_eligible]
```

Loop through shipping mode, market, region and customer segment, selecting eligible orders within each group. The input already has one row per order.


### Line 8–9

```text
  8              rows.append(dict(dimension=dim,segment=val,total_orders=len(g),eligible_orders=len(eligible),
  9                late_orders=int(eligible.late_order.sum()),late_delivery_rate=eligible.late_order.mean() if len(eligible) else None,
```

Report all orders, eligible orders and late orders separately; divide lateness by eligibility rather than treating invalid durations as punctual delivery.


### Line 10–11

```text
 10                average_delay_days=eligible.positive_delay_days.mean(),average_signed_delay=eligible.delay_days.mean(),
 11                actual_shipping_days=eligible.actual_shipping_days.mean(),scheduled_shipping_days=eligible.scheduled_shipping_days.mean()))
```

Report average positive delay, signed delay, actual duration and promised duration. Positive delay includes on-time zeros, so its denominator differs from average delay among late orders only.


### Line 12

```text
 12      return pd.DataFrame(rows)
```

Return stacked segment summaries; overlapping dimensions must not be added together.


### Line 13

```text
 13
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 14–16

```text
 14  def category_delivery(lines,delivery):
 15      # DISTINCT order-category, so a multi-category order appears once in each applicable category.
 16      x=lines[['order_id','category']].drop_duplicates().merge(delivery,on='order_id',validate='many_to_one')
```

Deduplicate order-category membership before attaching order delivery outcomes. Two lines of one category must not count as two deliveries.


### Line 17

```text
 17      return x.groupby('category').agg(orders=('order_id','nunique'),eligible_orders=('delivery_eligible','sum'),late_orders=('late_order','sum')).assign(late_delivery_rate=lambda x:x.late_orders/x.eligible_orders.replace(0,float('nan'))).reset_index()
```

Aggregate category order/eligible/late counts and rates, guarding zero denominators. A multi-category order belongs once to each relevant category; category totals are not additive to the overall order count.


## src/operations/delivery_risk_model.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws.


### Line 2

```text
  2  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 3

```text
  3  from sklearn.compose import ColumnTransformer
```

Import ColumnTransformer from sklearn.compose to provide classifier preprocessing, model pipelines, estimators and classification metrics.


### Line 4

```text
  4  from sklearn.preprocessing import OneHotEncoder,StandardScaler
```

Import OneHotEncoder, StandardScaler from sklearn.preprocessing to provide classifier preprocessing, model pipelines, estimators and classification metrics.


### Line 5

```text
  5  from sklearn.impute import SimpleImputer
```

Import SimpleImputer from sklearn.impute to provide classifier preprocessing, model pipelines, estimators and classification metrics.


### Line 6

```text
  6  from sklearn.pipeline import make_pipeline
```

Import make_pipeline from sklearn.pipeline to provide classifier preprocessing, model pipelines, estimators and classification metrics.


### Line 7

```text
  7  from sklearn.linear_model import LogisticRegression
```

Import LogisticRegression from sklearn.linear_model to provide classifier preprocessing, model pipelines, estimators and classification metrics.


### Line 8

```text
  8  from sklearn.tree import DecisionTreeClassifier
```

Import DecisionTreeClassifier from sklearn.tree to provide classifier preprocessing, model pipelines, estimators and classification metrics.


### Line 9

```text
  9  from sklearn.ensemble import RandomForestClassifier
```

Import RandomForestClassifier from sklearn.ensemble to provide classifier preprocessing, model pipelines, estimators and classification metrics.


### Line 10

```text
 10  from lightgbm import LGBMClassifier
```

Import LGBMClassifier from lightgbm to provide gradient-boosted tree estimators for demand regression or optional delivery classification.


### Line 11

```text
 11  from sklearn.metrics import precision_score,recall_score,f1_score,roc_auc_score,average_precision_score,confusion_matrix
```

Import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix from sklearn.metrics to provide classifier preprocessing, model pipelines, estimators and classification metrics.


### Line 12

```text
 12
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 13–14

```text
 13  def delivery_risk(delivery,seed=42):
 14      x=delivery[delivery.delivery_eligible].sort_values(['order_date','order_id']).copy()
```

Build the optional supervised model from eligible orders, sorted by date and ID, using late_order as the outcome.


### Line 15–16

```text
 15      dates=sorted(x.order_date.unique());cut=dates[int(.8*len(dates))]
 16      train=x[x.order_date<cut];test=x[x.order_date>=cut]
```

Split at 80% of unique dates so complete dates stay together and newer orders form the test. It is not exactly an 80% row split when daily volume varies.


### Line 17

```text
 17      if train.late_order.nunique()<2 or test.late_order.nunique()<2: raise ValueError('Risk model requires both outcomes in both time partitions')
```

Require both late/on-time examples in both partitions; metrics such as ROC-AUC cannot be meaningfully computed with a single outcome class.


### Line 18–19

```text
 18      cats=['shipping_mode','market','region','customer_segment'];numeric=['scheduled_shipping_days']
 19      features=cats+numeric
```

Use only shipping mode, market, region, segment and promised duration. Exclude actual duration, actual shipping date, source late flag and profit outcomes to avoid predicting with information learned after delivery.


### Line 20

```text
 20      prep=lambda:ColumnTransformer([('cats',OneHotEncoder(handle_unknown='ignore'),cats),('num',make_pipeline(SimpleImputer(),StandardScaler()),numeric)])
```

Build train-fitted preprocessing: one-hot categories with unknown-category handling and mean-imputed/scaled numeric promise. Creating this inside each pipeline prevents fitting preprocessing on the test set.


### Line 21–24

```text
 21      models={'logistic_regression':LogisticRegression(solver='liblinear',max_iter=1000,class_weight='balanced',random_state=seed),
 22       'decision_tree':DecisionTreeClassifier(max_depth=5,class_weight='balanced',random_state=seed),
 23       'random_forest':RandomForestClassifier(n_estimators=100,max_depth=8,class_weight='balanced',random_state=seed,n_jobs=2),
 24       'lightgbm':LGBMClassifier(n_estimators=100,class_weight='balanced',random_state=seed,n_jobs=2,verbosity=-1)}
```

Compare interpretable logistic regression, a shallow tree, a bounded random forest and LightGBM with balanced class weights. Fixed depths/tree counts are defaults; class weighting changes the fitted objective and can harm raw probability calibration.


### Line 25–28

```text
 25      rows=[];importance=[]
 26      for name,m in models.items():
 27          pipe=make_pipeline(prep(),m);pipe.fit(train[features],train.late_order.astype(int))
 28          p=pipe.predict_proba(test[features])[:,1]
```

Fit a fresh preprocessing/model pipeline on past orders and predict later-order probabilities. The local model dictionary uses a fixed two worker threads for ensembles.


### Line 29–30

```text
 29          if not np.isfinite(p).all(): raise ValueError('Non-finite delivery-risk predictions: '+name)
 30          pred=(p>=.5).astype(int);y=test.late_order.astype(int)
```

Reject nonfinite probabilities and convert to late/on-time using a fixed 0.5 threshold. The threshold is not tuned to operational false-alarm/missed-delay costs.


### Line 31–32

```text
 31          tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
 32          rows.append(dict(model=name,precision=precision_score(y,pred,zero_division=0),recall=recall_score(y,pred),f1=f1_score(y,pred),roc_auc=roc_auc_score(y,p),pr_auc=average_precision_score(y,p),tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp),threshold=.5))
```

Record confusion counts, precision, recall, F1, ROC-AUC and average precision. pr_auc here stores average_precision_score, which is not necessarily the same calculation as trapezoidal PR-curve area.


### Line 33–35

```text
 33          vals=m.coef_[0] if hasattr(m,'coef_') else m.feature_importances_
 34          importance.extend(dict(model=name,feature=f,importance=float(v)) for f,v in zip(pipe.steps[0][1].get_feature_names_out(),vals))
 35      return pd.DataFrame(rows),pd.DataFrame(importance)
```

Export logistic coefficients or tree importances with transformed feature names. These have different scales/meanings and are associational, not causal effects. No calibrated risk model or deployment artifact is saved.


## src/operations/profitability_analysis.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws.


### Line 2

```text
  2  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 3

```text
  3
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 4–6

```text
  4  def profitability(lines):
  5      good=lines[~lines.invalid_sales_flag]
  6      result=[]
```

Exclude rows explicitly flagged with negative sales/quantity and allocate result frames. Abnormal profits remain for review; missing numeric values are not automatically excluded by this flag.


### Line 7–8

```text
  7      for dim in ['category','market','region','product_name','customer_segment']:
  8          g=good.groupby(dim).agg(sales=('sales',lambda x:x.sum(min_count=1)),profit=('profit',lambda x:x.sum(min_count=1)),order_count=('order_id','nunique')).reset_index().rename(columns={dim:'segment'})
```

Group cleaned lines by each business dimension; sum sales/profit with min_count=1 so entirely unavailable money does not become zero, and count distinct orders.


### Line 9

```text
  9          g['dimension']=dim;g['profit_margin']=g.profit.div(g.sales.replace(0,np.nan));result.append(g)
```

Compute aggregate profit divided by aggregate sales, guarding zero. An average of line margins would overweight small transactions.


### Line 10–11

```text
 10      order=good.groupby('order_id').agg(sales=('sales',lambda x:x.sum(min_count=1)),profit=('profit',lambda x:x.sum(min_count=1))).reset_index()
 11      order['loss_making_order']=order.profit<0
```

Sum valid line values at order level before classifying a loss-making order. An order with one loss line can still have positive overall profit.


### Line 12

```text
 12      return pd.concat(result,ignore_index=True),order
```

Return both segment and order summaries for different business questions.


## src/utils/file_utils.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import json
```

Import json from json to provide readable structured audit/config/result records.


### Line 2

```text
  2  import re
```

Import re from re to provide regular-expression cleanup of source field names.


### Line 3

```text
  3  from pathlib import Path
```

Import Path from pathlib to provide portable filesystem paths; it avoids hard-coding slash separators and supports repository-relative locations.


### Line 4

```text
  4  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling. The imported name(s) pandas are not referenced elsewhere in this module’s executable syntax; they are cleanup opportunities rather than needed logic here.


### Line 5

```text
  5
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 6–7

```text
  6  def snake_case(s):
  7      return re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")
```

Normalize identifiers by trimming, lowercasing, replacing non-alphanumeric runs with underscores and stripping edge underscores. Ingestion separately rejects collisions after normalization.


### Line 8–9

```text
  8  def sql_literal(value):
  9      return "'" + str(value).replace("'", "''") + "'"
```

Quote a SQL string literal and escape apostrophes by doubling them. Used for controlled file paths; this is not a substitute for parameterized SQL everywhere.


### Line 10–11

```text
 10  def quote_identifier(value):
 11      return '"' + str(value).replace('"', '""') + '"'
```

Quote a SQL identifier with double quotes and escape embedded quotes. Column names and string values use different SQL quoting rules.


### Line 12–14

```text
 12  def write_json(path, obj):
 13      Path(path).parent.mkdir(parents=True, exist_ok=True)
 14      Path(path).write_text(json.dumps(obj, indent=2, default=str, allow_nan=False))
```

Ensure the parent directory exists and write readable JSON. default=str supports dates/paths; allow_nan=False rejects nonstandard NaN/Infinity instead of silently creating invalid JSON.


### Line 15–16

```text
 15  def export_frame(df, name, out):
 16      out=Path(out);out.mkdir(parents=True,exist_ok=True)
```

Create the export directory for a named DataFrame.


### Line 17–18

```text
 17      df.to_parquet(out / (name+".parquet"), index=False)
 18      df.to_csv(out / (name+".csv"), index=False)
```

Write Parquet for typed/efficient analysis and CSV for convenient inspection/import, omitting the incidental Pandas row index. Writing both uses more disk space.


### Line 19

```text
 19      return df
```

Return the original frame for convenient composition; most callers rely only on file outputs.


## src/utils/metrics.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws.


### Line 2

```text
  2
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 3–4

```text
  3  def rmsse_scale(y):
  4      y=np.asarray(y,dtype=float);nz=np.flatnonzero(y)
```

Convert training history to floats and locate nonzero observations for a scale independent of leading pre-sale zeros.


### Line 5–7

```text
  5      if len(nz)==0: return np.nan
  6      y=y[nz[0]:]
  7      return float(np.mean(np.diff(y)**2)) if len(y)>1 and np.any(np.diff(y)) else np.nan
```

Return undefined for all-zero or constant histories; otherwise remove leading zeros and average squared first differences. This is the per-series RMSSE denominator, calculated from training history only.


### Line 8

```text
  8
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 9–11

```text
  9  def metrics(actual,pred,scales=None):
 10      y=np.asarray(actual,float);p=np.asarray(pred,float);e=p-y
 11      total=y.sum();valid=y!=0
```

Convert actual/predicted arrays and form signed error as forecast minus actual. Identify nonzero actuals for percentage error and the total actual denominator.


### Line 12

```text
 12      result={'mae':float(np.abs(e).mean()),'rmse':float(np.sqrt(np.mean(e**2))),
```

MAE averages absolute unit error; RMSE square-roots mean squared error and therefore emphasizes large mistakes.


### Line 13

```text
 13       'wape':float(np.abs(e).sum()/total) if total else np.nan,
```

WAPE is total absolute error divided by total actual demand; return NaN when total actual is zero. This portfolio score emphasizes high-volume observations.


### Line 14

```text
 14       'mape':float(np.mean(np.abs(e[valid]/y[valid]))) if valid.any() else np.nan,
```

MAPE averages percentage errors only where actual is nonzero. This avoids division by zero but excludes zero-demand days and can overemphasize tiny denominators.


### Line 15

```text
 15       'bias':float(e.sum()/total) if total else np.nan,'rmsse':np.nan}
```

Normalized bias retains error sign to reveal systematic over/underprediction; cancellation is useful for bias, not an accuracy measure. Initialize RMSSE undefined unless scales are provided.


### Line 16–18

```text
 16      if scales is not None:
 17          s=np.asarray(scales,float);v=np.isfinite(s)&(s>0)
 18          if v.any(): result['rmsse']=float(np.sqrt(np.mean(e[v]**2/s[v])))
```

For valid positive series scales, average normalized squared errors across rows and take the square root. This is pooled bottom-level RMSSE, not the official M5 hierarchical revenue-weighted WRMSSE.


### Line 19

```text
 19      return result
```

Return the named metric dictionary, which reporting can expand into a result row.


## src/analysis.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws.


### Line 2

```text
  2  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling. The imported name(s) pandas are not referenced elsewhere in this module’s executable syntax; they are cleanup opportunities rather than needed logic here.


### Line 3

```text
  3  from src.utils.file_utils import export_frame
```

Import export_frame from src.utils.file_utils to provide reuse src/utils/file_utils.py rather than duplicating that stage’s implementation.


### Line 4

```text
  4
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 5–10

```text
  5  def history_summary(con,origin):
  6      return con.execute("""SELECT item_id,store_id,category_id,department_id,state_id,
  7         avg(units_sold) average_daily_demand,stddev_samp(units_sold) demand_std,
  8         sum(revenue) revenue,sum(units_sold) units_sold,
  9         avg(zero_sales_flag) zero_demand_share,arg_max(sell_price,date) last_price
 10         FROM sales WHERE date<=? AND date>? - INTERVAL '90 days' GROUP BY ALL""",[origin,origin]).df()
```

Summarize the last 90 days available at an origin for each item-store: mean/std of units, revenue, zero share and latest nonnull price. A recent window captures current behavior while excluding future dates; 90 is a fixed heuristic here.


### Line 11

```text
 11
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 12–14

```text
 12  def segmentation(history,cfg):
 13      x=history.sort_values(['revenue','item_id','store_id'],ascending=[False,True,True]).copy()
 14      total=x.revenue.sum();prior=(x.revenue.cumsum()-x.revenue)/(total or 1)
```

Sort revenue descending with stable ties, then compute cumulative revenue share before each item. Using prior share keeps the item that crosses a cutoff in the higher class.


### Line 15

```text
 15      x['abc']=np.select([prior<.8,prior<.95],['A','B'],default='C') if total>0 else 'C'
```

Assign A through the 80% crossing, B through 95%, otherwise C. These are planning heuristics, not natural laws; all-zero revenue maps to C.


### Line 16

```text
 16      x['coefficient_of_variation']=x.demand_std/x.average_daily_demand.replace(0,np.nan)
```

Compute coefficient of variation (standard deviation/mean); zero mean gives undefined rather than infinity.


### Line 17–18

```text
 17      a,b=cfg['xyz_cv_thresholds'];x['xyz']=np.select([(x.coefficient_of_variation<=a)&(x.zero_demand_share<cfg['intermittent_zero_share']),
 18          (x.coefficient_of_variation<=b)&(x.zero_demand_share<cfg['intermittent_zero_share'])],['X','Y'],default='Z')
```

Assign X/Y only if variability is low/moderate and zero-sales share is below the intermittent threshold; otherwise Z. Frequent zero sales should not look stable merely because their absolute variation is small.


### Line 19–21

```text
 19      x['abc_xyz']=x.abc+'-'+x.xyz
 20      q=x.average_daily_demand.rank(pct=True,method='average');x['volume_segment']=np.select([q<=1/3,q<=2/3],['low','medium'],default='high')
 21      x['cumulative_revenue_share']=x.revenue.cumsum()/(total or 1)
```

Combine ABC/XYZ, add relative demand-volume terciles and final cumulative share. Rank ties can prevent exactly equal thirds.


### Line 22

```text
 22      return x
```

Return enriched pair-level data for analysis and segment-level forecast assessment.


### Line 23

```text
 23
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 24–27

```text
 24  def eda(con,lines,delivery,cfg,out):
 25      tables={}
 26      for name,grain in [('sales_monthly',"date_trunc('month',date)"),('sales_weekly',"date_trunc('week',date)"),('sales_trend','date')]:
 27          tables[name]=con.execute(f'SELECT {grain} period,sum(units_sold) units_sold,sum(revenue) revenue FROM sales GROUP BY 1 ORDER BY 1').df()
```

Create daily, weekly and monthly total sales trends to expose seasonality at different resolutions. They are alternate aggregations of the same sales.


### Line 28–29

```text
 28      for col in ['category_id','department_id','item_id','store_id','state_id','weekday','month','event_name','snap_flag']:
 29          tables['m5_by_'+col]=con.execute(f'SELECT {col},sum(units_sold) units_sold,sum(revenue) revenue,avg(units_sold) mean_series_day_units,count(*) series_days FROM sales GROUP BY 1').df()
```

Summarize products, stores, dates, events and SNAP using totals, average units per series-day and exposure counts. Comparing totals alone can confuse more observations with stronger demand.


### Line 30

```text
 30      tables['price_demand_association']=con.execute('SELECT item_id,store_id,corr(price_change_percentage,units_sold) price_change_demand_correlation FROM features GROUP BY ALL').df()
```

Calculate historical within-pair correlation of price change with demand. This is descriptive and can be undefined for constant prices; it does not estimate causal price elasticity.


### Line 31–33

```text
 31      end=con.execute('SELECT max(date) FROM sales').fetchone()[0]
 32      tables['product_store_performance']=segmentation(history_summary(con,end),cfg)
 33      tables['abc_xyz_segmentation']=tables['product_store_performance'][['item_id','store_id','abc','xyz','abc_xyz','volume_segment','coefficient_of_variation','cumulative_revenue_share']]
```

Create current product-store performance and classification exports. These use the final history date; the evaluation path separately freezes its segments at the test origin.


### Line 34–35

```text
 34      monthly=lines.assign(period=lines.order_date.dt.to_period('M').dt.to_timestamp()).groupby('period').agg(sales=('sales','sum'),profit=('profit','sum'),orders=('order_id','nunique')).reset_index()
 35      tables['dataco_monthly']=monthly
```

Create DataCo monthly sales/profit/distinct-order summaries. Unlike profitability(), this block does not exclude invalid_sales_flag rows and uses ordinary sums; reconcile definitions before comparing these totals on messy real data.


### Line 36–37

```text
 36      for name,x in tables.items(): export_frame(x,name,out)
 37      return tables
```

Write all summaries and return them. The function's delivery argument is currently unused.


## src/fixtures.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  """Deterministic synthetic integration inputs; never masquerade as M5/DataCo."""
```

Identify the file as a synthetic integration generator; its values must not be described as actual Walmart/DataCo evidence.


### Line 2

```text
  2  from pathlib import Path
```

Import Path from pathlib to provide portable filesystem paths; it avoids hard-coding slash separators and supports repository-relative locations.


### Line 3

```text
  3  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws.


### Line 4

```text
  4  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 5

```text
  5
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 6–7

```text
  6  def create_fixture(root,seed=42):
  7      root=Path(root);m5=root/'m5';dc=root/'dataco';m5.mkdir(parents=True,exist_ok=True);dc.mkdir(parents=True,exist_ok=True)
```

Accept output folder/seed and create separate M5/DataCo fixture folders.


### Line 8

```text
  8      rng=np.random.default_rng(seed);days=600;dates=pd.date_range('2015-01-01',periods=days+120)
```

Generate a reproducible random stream, 600 observed days and 120 extra calendar days. Future calendar coverage allows backtests and production forecasts without future target values.


### Line 9

```text
  9      cal=pd.DataFrame({'date':dates,'wm_yr_wk':np.arange(len(dates))//7+1000,'d':['d_'+str(i+1) for i in range(len(dates))]})
```

Create synthetic week/day identifiers and dates matching the expected M5 shape. The week numbering is an artificial 7-day grouping, not the official Walmart calendar.


### Line 10

```text
 10      for state in ['CA','TX','WI']: cal['snap_'+state]=(dates.day<=10).astype(int)
```

Create simple first-ten-days SNAP flags for each state. These exercise state-specific feature logic and are not real benefit schedules.


### Line 11–13

```text
 11      event=np.arange(len(dates))%60==0
 12      cal['event_name_1']=np.where(event,'Synthetic Festival',None);cal['event_type_1']=np.where(event,'Cultural',None)
 13      cal['event_name_2']=None;cal['event_type_2']=None;cal.to_csv(m5/'calendar.csv',index=False)
```

Insert a periodic fictional festival and empty second-event slots, then write calendar CSV.


### Line 14–17

```text
 14      sales=[];prices=[]
 15      for store,state in [('CA_1','CA'),('TX_1','TX'),('WI_1','WI')]:
 16          for item in range(1,13):
 17              iid=f'SYNTH_{item:03d}';price=2+item*.7
```

Prepare sales/prices for 12 synthetic products in three stores with deterministic product IDs and prices.


### Line 18

```text
 18              mean=(item%5+1)*(1+.35*(dates[:days].dayofweek>=5))*(1+.5*event[:days])
```

Construct mean demand with a weekend increase and festival increase so models have learnable calendar patterns.


### Line 19

```text
 19              demand=rng.poisson(mean);demand=demand*(rng.random(days)>.55) if item%5==0 else demand
```

Draw Poisson counts; every fifth product gets extra zero-demand days to exercise intermittent-demand logic. This artificially favorable data-generating family is one reason fixture accuracy cannot predict real-data performance.


### Line 20–23

```text
 20              row=dict(id=iid+'_'+store+'_evaluation',item_id=iid,dept_id='D'+str(item%3),cat_id='C'+str((item%3)%2),store_id=store,state_id=state)
 21              row.update({'d_'+str(j+1):int(v) for j,v in enumerate(demand)});sales.append(row)
 22              prices.extend(dict(store_id=store,item_id=iid,wm_yr_wk=int(w),sell_price=price) for w in cal.wm_yr_wk.unique())
 23      pd.DataFrame(sales).to_csv(m5/'sales_train_evaluation.csv',index=False);pd.DataFrame(prices).to_csv(m5/'sell_prices.csv',index=False)
```

Write M5-compatible metadata, one column per observed day, and weekly prices. Category/department assignments are constructed to remain internally consistent.


### Line 24–26

```text
 24      orders=[];line=0
 25      for order in range(1,241):
 26          date=pd.Timestamp('2016-01-01')+pd.Timedelta(days=order//2);scheduled=int(rng.choice([2,4]));actual=max(1,scheduled+int(rng.choice([-1,0,0,1,2,3])))
```

Create 240 orders with synthetic order dates, scheduled durations and randomized early/on-time/late actual durations.


### Line 27–28

```text
 27          for j in range(int(rng.integers(1,4))):
 28              line+=1;sales=float(rng.uniform(20,200));profit=sales*float(rng.uniform(-.2,.3))
```

Give each order one to three lines and draw line-level sales/profit, including some losses. This explicitly tests that deliveries and profitability use different grains.


### Line 29–34

```text
 29              orders.append({'Order Id':order,'Order Item Id':line,'order date (DateOrders)':date,'shipping date (DateOrders)':date+pd.Timedelta(days=actual),
 30               'Days for shipping (real)':actual,'Days for shipment (scheduled)':scheduled,'Late_delivery_risk':int(actual>scheduled),
 31               'Shipping Mode':'Standard Class' if scheduled==4 else 'Second Class','Market':'Europe' if order%2 else 'USCA',
 32               'Order Region':'West' if order%2 else 'East','Category Name':'Synthetic Category '+str(j%2),'Customer Segment':'Consumer',
 33               'Product Name':'Synthetic Product '+str(j),'Order Item Quantity':2,'Order Item Total':sales,'Sales':sales,
 34               'Benefit per order':profit,'Order Profit Per Order':profit,'Order Item Profit Ratio':profit/sales,'Order Status':'Complete',
```

Populate expected DataCo field names, consistent order-level shipment attributes and varying line-level products/categories.


### Line 35

```text
 35               'Customer Fname':'PRIVATE_TEST_NAME','Customer Email':'private@example.invalid','Customer Password':'DO_NOT_EXPORT'})
```

Add clearly fictional sensitive-field sentinels so tests can prove the ingestion allowlist removes those columns/values. These are not real credentials.


### Line 36–38

```text
 36      pd.DataFrame(orders).to_csv(dc/'DataCoSupplyChainDataset.csv',index=False,encoding='utf-8')
 37      (root/'SYNTHETIC_FIXTURE.txt').write_text('Generated synthetic integration data. No real retailer observations.\n')
 38      return m5,dc
```

Write DataCo CSV and a plain synthetic-data marker, then return both input folders for the same production transformation functions.


## src/recommendations.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  """Recommendations quote calculated evidence and never imply causal or achieved impact."""
```

State that recommendations must cite computed evidence and must not claim causal or achieved savings.


### Line 2

```text
  2  from pathlib import Path
```

Import Path from pathlib to provide portable filesystem paths; it avoids hard-coding slash separators and supports repository-relative locations.


### Line 3

```text
  3  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 4

```text
  4
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 5–8

```text
  5  def recommendations(out, fixture):
  6      out=Path(out);read=lambda n:pd.read_parquet(out/(n+'.parquet'));rows=[]
  7      provenance='synthetic_fixture' if fixture else 'kaggle'
  8      def emit(domain,kind,action,evidence,source): rows.append(dict(domain=domain,evidence_type=kind,recommendation=action,evidence=evidence,source_table=source,data_provenance=provenance))
```

Set up an output-table reader and a helper that attaches domain, evidence type, source table and provenance to every recommendation.


### Line 9–11

```text
  9      policy=read('inventory_policy_recommendations').query('target_service_level == 0.95')
 10      r=policy.sort_values('stockout_probability',ascending=False).iloc[0]
 11      emit('M5','scenario','Verify starting stock and consider a larger buffer for '+r.item_id+'/'+r.store_id,f'Modeled stockout probability {r.stockout_probability:.4f}; safety stock {r.safety_stock:.2f} units','inventory_policy_recommendations')
```

At a hard-coded 95% service target, find highest modeled opening-stock risk and recommend verification/buffer review. This assumes 0.95 is in configuration; removing it can break the report path.


### Line 12–14

```text
 12      excess=policy.sort_values('excess_value',ascending=False)
 13      if len(excess) and excess.iloc[0].excess_value>0:
 14          r=excess.iloc[0];emit('M5','scenario','Review lower replenishment for '+r.item_id+'/'+r.store_id,f'Assumed excess {r.excess_units:.2f} units; value {r.excess_value:.2f}','inventory_policy_recommendations')
```

Recommend checking excess only if modeled excess value is positive, avoiding a fabricated excess-stock issue.


### Line 15–16

```text
 15      accuracy=read('forecast_accuracy_by_segment').query("segment_type == 'store_id'").sort_values('wape',ascending=False)
 16      r=accuracy.iloc[0];emit('M5','forecast_evaluation','Prioritize forecast-error review in store '+r.segment,f'Locked-test WAPE {r.wape:.4f}','forecast_accuracy_by_segment')
```

Prioritize the store with worst locked-test WAPE for forecast investigation. A worst rank alone does not prove a significant difference or identify its cause.


### Line 17–18

```text
 17      perf=read('product_store_performance');z=perf[perf.xyz=='Z']
 18      if len(z): emit('M5','historical','Evaluate intermittent-demand methods for Z items',f'{len(z)} item-store pairs classified Z of {len(perf)}; cutoff zero-share 0.5 or configured high CV','product_store_performance')
```

Suggest intermittent-demand methods when Z-class pairs exist. The text mentions 0.5 even though the actual zero-share cutoff is configurable, a wording limitation if configuration changes.


### Line 19–20

```text
 19      cat=policy.groupby('category_id').safety_stock.mean().sort_values(ascending=False)
 20      emit('M5','scenario','Review separate inventory buffers for category '+str(cat.index[0]),f'Mean safety stock {cat.iloc[0]:.2f} units at 95% assumed service','inventory_policy_recommendations')
```

Identify the category with highest average safety stock. Averaging units is a descriptive screen; it does not control for differing volumes, costs or item counts.


### Line 21–23

```text
 21      ev=read('m5_by_event_name').dropna(subset=['event_name']).sort_values('mean_series_day_units',ascending=False)
 22      if len(ev):
 23          r=ev.iloc[0];emit('M5','historical','Review event calendar ahead of '+r.event_name,f'Observed mean {r.mean_series_day_units:.3f} units per series-day across {r.series_days} observations; unadjusted for seasonality','m5_by_event_name')
```

Show the event with strongest observed mean series-day sales while explicitly acknowledging unadjusted seasonality. This is not an estimated causal event effect.


### Line 24–28

```text
 24      ship=read('dataco_shipping_mode_performance')
 25      for dim in ['shipping_mode','market']:
 26          z=ship[ship.dimension==dim].dropna(subset=['late_delivery_rate']).sort_values('late_delivery_rate',ascending=False)
 27          if len(z):
 28              r=z.iloc[0];emit('DataCo','historical','Investigate promise-setting and capacity for '+str(r.segment),f'{r.late_orders}/{r.eligible_orders} eligible orders late ({r.late_delivery_rate:.4f}); association only','dataco_shipping_mode_performance')
```

Find highest valid late share for mode and market and cite numerator/denominator. Recommend investigation, not an unsupported claim about why delays happen.


### Line 29–33

```text
 29      profits=read('dataco_profitability_summary').query("dimension == 'category'")
 30      if profits.sales.notna().any():
 31          top=profits[profits.sales>=profits.sales.quantile(.75)].sort_values('profit_margin')
 32          if len(top):
 33              r=top.iloc[0];emit('DataCo','historical','Review pricing, mix and discount leakage for '+r.segment,f'Top-quartile category sales {r.sales:.2f}; margin {r.profit_margin:.4f}; no causal attribution','dataco_profitability_summary')
```

Among top-quartile sales categories, identify low margin for pricing/mix review. The source table excludes invalid sales rows; the recommendation is a hypothesis, not proof of discount leakage.


### Line 34–38

```text
 34      k=read('inventory_simulation_kpis').query("policy == 'optimized'")
 35      for service,g in k.groupby('target_service_level'):
 36          savings=g.groupby('run_id').estimated_cost_reduction.sum().mean()
 37          fill=g.fulfilled_units.sum()/g.actual_demand.sum() if g.actual_demand.sum() else float('nan')
 38          emit('M5','scenario',f'Compare cost/service before adopting the {service:.0%} target',f'Paired estimated cost reduction {savings:.2f}; demand-weighted fill rate {fill:.4f}; negative savings indicate higher cost','inventory_simulation_kpis')
```

For each service target, sum paired savings within each run then average runs, calculate demand-weighted fill rate and retain negative savings. This frames the decision as cost versus service.


### Line 39

```text
 39      return pd.DataFrame(rows)
```

Return evidence-backed actions as data so both reports and dashboards can expose their supporting tables.


## src/reporting.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  from pathlib import Path
```

Import Path from pathlib to provide portable filesystem paths; it avoids hard-coding slash separators and supports repository-relative locations.


### Line 2

```text
  2  import json
```

Import json from json to provide readable structured audit/config/result records. The imported name(s) json are not referenced elsewhere in this module’s executable syntax; they are cleanup opportunities rather than needed logic here.


### Line 3

```text
  3  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling. The imported name(s) pandas are not referenced elsewhere in this module’s executable syntax; they are cleanup opportunities rather than needed logic here.


### Line 4

```text
  4  from src.utils.file_utils import write_json
```

Import write_json from src.utils.file_utils to provide reuse src/utils/file_utils.py rather than duplicating that stage’s implementation. The imported name(s) write_json are not referenced elsewhere in this module’s executable syntax; they are cleanup opportunities rather than needed logic here.


### Line 5

```text
  5
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 6–8

```text
  6  def write_reports(out,reports,mode,fixture,champion,comparison,test,kpis,shipping,policy):
  7      reports=Path(reports);reports.mkdir(parents=True,exist_ok=True)
  8      label='SYNTHETIC FIXTURE — engineering validation only' if fixture else 'Kaggle source data — selected cohort' if mode=='sample' else 'Kaggle source data — full cohort'
```

Create the report folder and choose an explicit synthetic/sample/full provenance label for every narrative/chart.


### Line 9

```text
  9      best=comparison[(comparison.split_role=='test')&(comparison.model==champion)&(comparison.forecast_level=='item_store')].iloc[0]
```

Select the winner's locked-test item-store score rather than its selection score or a different aggregation level.


### Line 10–12

```text
 10      service=.95
 11      k=kpis[(kpis.target_service_level==service)&(kpis.policy=='optimized')]
 12      cost=k.groupby('run_id').total_inventory_cost.sum().mean();saving=k.groupby('run_id').estimated_cost_reduction.sum().mean()
```

Use a hard-coded .95 service slice and average per-run portfolio cost/savings. This should eventually use the configured default and handle missing slices safely.


### Line 13–15

```text
 13      ship=shipping[shipping.dimension=='shipping_mode'].sort_values('late_delivery_rate',ascending=False)
 14      worst=ship.iloc[0]
 15      risk=policy[policy.target_service_level==service].sort_values('stockout_probability',ascending=False).iloc[0]
```

Find the mode with greatest late rate and pair with greatest modeled stock risk. Empty inputs or a missing 95% policy are not guarded here; iloc[0] can fail.


### Line 16–19

```text
 16      text=f"""# Executive evidence report
 17
 18  Data provenance: **{label}**. Forecasts are estimates; inventory economics are simulated scenario estimates.
 19  No savings represent measured operational changes. M5 and DataCo are independent domains.
```

Begin a templated Markdown report with source provenance and an explicit distinction between estimates and operational results.


### Line 20

```text
 20
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 21–24

```text
 21  ## Forecast evidence
 22  Selected model: `{champion}` using the pre-test selection fold. Held-out WAPE: {best.wape:.2%}; MAE: {best.mae:.3f}; normalized bias: {best.bias:.2%}.
 23  Empirical held-out interval coverage: 80% band {test.covered_80.mean():.2%}; 95% band {test.covered_95.mean():.2%}.
 24  Source: `forecast_model_metrics`, `forecast_backtest_selected`.
```

Insert model choice, test error/bias and empirical interval coverage with source-table names so a reader can reproduce the figures.


### Line 25

```text
 25
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 26–32

```text
 26  ## Inventory scenario evidence
 27  At 95% target service, optimized average total cost across runs: {cost:,.2f} currency units.
 28  Baseline minus optimized cost: {saving:,.2f} currency units (negative means optimized costs more).
 29  Source: `inventory_simulation_kpis`; preserve service level and average across runs before aggregation.
 30  Highest modeled starting-stock risk: {risk.item_id}/{risk.store_id}, probability {risk.stockout_probability:.2%}.
 31  Source: `stockout_risk`; assumes no initial purchase orders and simulated opening inventory.
 32  Recommendation: verify lead times and opening stock for this pair before applying its replenishment recommendation.
```

Insert modeled cost, baseline difference and starting-stock risk. Negative cost reduction is described honestly, and the stock recommendation requires validating real inputs.


### Line 33

```text
 33
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 34–36

```text
 34  ## Logistics evidence
 35  Shipping mode with largest observed late share: {worst.segment}, {worst.late_orders:,.0f}/{worst.eligible_orders:,.0f} eligible orders ({worst.late_delivery_rate:.2%}).
 36  Source: `dataco_shipping_mode_performance`. Investigate capacity and promise-setting; association does not establish cause.
```

Insert late-order counts/rate and an investigation suggestion, explicitly avoiding causal attribution.


### Line 37

```text
 37
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 38–43

```text
 38  ## Decision gates
 39  Pilot inventory changes only after validating real procurement costs, inventory positions and supplier distributions.
 40  Evaluate profit and service trade-offs across `inventory_sensitivity`; do not select a policy solely for lower stockouts.
 41  Review sparse segments and uncertainty before stocking for event-associated uplift. SNAP is benefit eligibility, not a promotion flag.
 42  If this report uses fixtures, every observation above describes the synthetic fixture only and is not a business finding.
 43  """
```

State decision gates: verify assumptions, evaluate service/cost trade-offs and avoid claiming fixture patterns or SNAP flags are real business/promotion evidence.


### Line 44–45

```text
 44      (reports/'executive_summary.md').write_text(text)
 45      (reports/'model_performance.md').write_text('# Model performance\n\n'+label+'\n\n'+comparison.to_csv(index=False)+'\nRMSSE is pooled normalized squared error at bottom level, not official hierarchical WRMSSE. Aggregate ETS/SARIMA rows are a separate forecast level and are not candidates for item-store replenishment.\n')
```

Save executive and model-performance documents. The second file embeds CSV text and explains why pooled RMSSE and aggregate diagnostics are not official M5 benchmark results.


### Line 46–48

```text
 46      import matplotlib
 47      matplotlib.use('Agg')
 48      import matplotlib.pyplot as plt
```

Select Matplotlib's noninteractive Agg backend before importing pyplot so chart generation works without a desktop window.


### Line 49–51

```text
 49      trend=test.groupby('date')[['actual_units','forecast_units','lower_80','upper_80']].sum()
 50      fig,ax=plt.subplots(figsize=(11,4));ax.plot(trend.index,trend.actual_units,label='Actual');ax.plot(trend.index,trend.forecast_units,label='Forecast')
 51      ax.set(title=label+' | held-out demand',ylabel='Units');ax.legend();fig.autofmt_xdate();fig.tight_layout();fig.savefig(reports/'forecast_validation.png',dpi=160);plt.close(fig)
```

Aggregate test actual/point forecasts by day, plot them, save PNG and close the figure to release memory. Interval columns are aggregated into trend but not plotted; summed marginal bounds would not automatically be calibrated portfolio intervals.


### Line 52–54

```text
 52      import plotly.express as px
 53      fig=px.bar(comparison[comparison.forecast_level=='item_store'],x='model',y='wape',color='split_role',barmode='group',title=label+' | forecast comparison')
 54      fig.write_html(reports/'model_comparison.html',include_plotlyjs=True)
```

Build a self-contained Plotly comparison HTML with embedded JavaScript. Multiple folds with the same calibration role can appear as repeated bars if folds>3; the default has one of each role.


### Line 55

```text
 55
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 56–58

```text
 56  def output_dictionary(out,root):
 57      import pyarrow.parquet as pq
 58      descriptions={
```

Start a schema-driven dictionary generator with manually specified field meanings; this documents outputs actually written by the run.


### Line 59–64

```text
 59        'forecast_units':('forecast','Predicted unit demand for date and model; sum only one model/origin'),
 60        'actual_units':('observed','Held-out recorded sales units, not uncensored demand'),
 61        'units_sold':('observed','Recorded M5 sales units'),
 62        'revenue':('derived','Units sold multiplied by weekly selling price; zero when zero units'),
 63        'sales':('observed','DataCo configured line net sales field; currency per source'),
 64        'profit':('observed','DataCo configured line benefit field; validate source semantics'),
```

Define forecast/actual/sales/revenue/profit provenance and semantics, especially recorded versus latent demand and source-specific monetary meanings.


### Line 65–72

```text
 65        'target_service_level':('simulated','Assumed cycle-service probability, not fill rate'),
 66        'stockout_probability':('simulated','Normal lead-time-demand tail at assumed starting stock'),
 67        'date_key':('derived','YYYYMMDD integer key'),
 68        'scale':('derived','Mean squared training first difference after first nonzero sale'),
 69        'inventory_value':('simulated','Initial units multiplied by estimated unit cost'),
 70        'rmsse':('derived','Square root of pooled squared error divided by per-series training scale'),
 71        'bias':('derived','Sum(forecast-actual)/sum(actual); positive is overforecast'),
 72        'wape':('derived','Sum absolute errors / sum actual; null for zero denominator'),
```

Define simulated service/risk/investment and derived metric/date/scale fields so readers do not confuse estimates with measured inputs.


### Line 73–80

```text
 73        'late_order':('derived','Actual shipping duration > scheduled duration; null if ineligible'),
 74        'delay_days':('derived','Actual minus scheduled shipping duration, signed'),
 75        'positive_delay_days':('derived','max(delay_days,0), eligible orders only'),
 76        'run_id':('simulated','Monte Carlo repetition; average costs across runs, never sum repeated worlds'),
 77        'scenario':('simulated','One-factor-at-a-time assumption scenario'),
 78        'policy':('simulated','Baseline or forecast-driven optimized replenishment rule'),
 79        'split_role':('derived','Calibration, selection, or locked test chronological window'),
 80        'origin':('derived','Last historical date available to the forecast'),
```

Define delivery timing, simulation dimensions, split roles and origins. These fields determine valid denominators and which records may be aggregated together.


### Line 81–85

```text
 81        'item_id':('observed','M5 product natural key'), 'store_id':('observed','M5 store natural key'),
 82        'date':('observed','Calendar date; forecast dates refer to known future calendar'),
 83        'order_id':('observed','DataCo business order key; not a customer identifier'),
 84        'order_item_id':('observed','DataCo unique order-line key'),
 85      }
```

Define business identifiers/date fields; order_id is an order key rather than a customer identifier. A field-level observed label is semantic: the run-level fixture label still says its values are synthetic.


### Line 86–88

```text
 86      import yaml
 87      explicit=yaml.safe_load((Path(root)/'config/field_definitions.yaml').read_text())
 88      descriptions.update({name:(value['provenance'],value['definition']) for name,value in explicit.items()})
```

Load explicit YAML definitions and override built-in entries. This keeps detailed definitions editable without changing report code.


### Line 89–96

```text
 89      tables={}
 90      for path in sorted(Path(out).glob('*.parquet')):
 91          schema=pq.read_schema(path);fields={}
 92          for f in schema:
 93              default='simulated' if path.stem.startswith(('inventory','stockout','excess')) else 'derived'
 94              kind,definition=descriptions.get(f.name,(default,f.name.replace('_',' ').capitalize()+'; see generating module and table grain below.'))
 95              fields[f.name]={'type':str(f.type),'provenance':kind,'definition':definition}
 96          tables[path.stem]=fields
```

Read every exported Parquet schema and record each field's exact type, provenance and description. Unknown fields get a generic fallback, which is weaker documentation than a manually reviewed definition.


### Line 97–98

```text
 97      import yaml
 98      (Path(root)/'config/data_dictionary.yaml').write_text(yaml.safe_dump(tables,sort_keys=False))
```

Write the machine-readable dictionary. The second import yaml is redundant and can be removed without changing behavior.


### Line 99–103

```text
 99      text=['# Output field dictionary','Generated from the executed Parquet schemas. Currency units are source-specific; never add M5 and DataCo money.','Null means unavailable or undefined, never automatically zero. Each forecast has one origin/model; every simulation row includes policy, service, scenario and run.']
100      for name,fields in tables.items():
101          text+=['\n## '+name,'| Field | Type | Provenance | Definition |','|---|---|---|---|']
102          text += [f"| {c} | {v['type']} | {v['provenance']} | {v['definition']} |" for c,v in fields.items()]
103      (Path(root)/'docs/data_dictionary.md').write_text('\n'.join(text)+'\n')
```

Write the human-readable field dictionary with cautions about currencies, nulls and scenario/model grain, then one table per output. This overwrites the prior dictionary with the current run's export set.


## src/database.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  """Transactional reload of this project's schemas only. Stream Parquet batches into PostgreSQL."""
```

Document atomic reload of project tables using streamed Parquet batches. File generation before this step is not part of this database transaction.


### Line 2

```text
  2  import os
```

Import os from os to provide environment variables, here database configuration.


### Line 3

```text
  3  from pathlib import Path
```

Import Path from pathlib to provide portable filesystem paths; it avoids hard-coding slash separators and supports repository-relative locations.


### Line 4

```text
  4  import pyarrow.parquet as pq
```

Import pyarrow.parquet as pq from pyarrow.parquet to provide Parquet schemas and typed batch reads.


### Line 5

```text
  5  from sqlalchemy import create_engine,inspect,text
```

Import create_engine, inspect, text from sqlalchemy to provide database connection/transaction, schema inspection and Pandas SQL integration. The imported name(s) text are not referenced elsewhere in this module’s executable syntax; they are cleanup opportunities rather than needed logic here.


### Line 6

```text
  6  from dotenv import load_dotenv
```

Import load_dotenv from dotenv to provide local .env configuration rather than hardcoded secrets.


### Line 7

```text
  7
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 8–14

```text
  8  MAPPING=[('dim_date','common','dim_date'),('dim_state','m5','dim_state'),('dim_category','m5','dim_category'),
  9   ('dim_department','m5','dim_department'),('dim_store','m5','dim_store'),('dim_product','m5','dim_product'),('dim_event','m5','dim_event'),('bridge_date_event','m5','bridge_date_event'),
 10   ('dim_order_date','dataco','dim_order_date'),('dim_product_category','dataco','dim_product_category'),('dim_market','dataco','dim_market'),('dim_region','dataco','dim_region'),('dim_shipping_mode','dataco','dim_shipping_mode'),('dim_customer_segment','dataco','dim_customer_segment'),
 11   ('sales_daily','m5','fact_sales_daily'),('fact_sell_price','m5','fact_sell_price'),('dataco_delivery_performance','dataco','fact_delivery_performance'),
 12   ('dataco_profitability','dataco','fact_orders'),('dataco_profitability','dataco','fact_profitability'),
 13   ('demand_forecasts_28d','m5','fact_forecast'),('forecast_backtest_all','m5','fact_forecast_accuracy'),
 14   ('inventory_policy_recommendations','m5','fact_inventory_policy'),('inventory_simulation_daily','m5','fact_inventory_simulation')]
```

Map each export to a schema/table in dependency order: dimensions, deliveries/lines, forecasts and simulations. The DataCo line export supplies two narrower database tables, not two independent sets of transactions.


### Line 15

```text
 15
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 16–19

```text
 16  def load_database(out,sql_dir):
 17      load_dotenv();url=os.environ.get('DATABASE_URL')
 18      if not url: raise ValueError('DATABASE_URL must be configured; use .env.example')
 19      engine=create_engine(url)
```

Load .env/environment configuration, require a database URL and construct a SQLAlchemy engine. Secrets are read locally rather than hardcoded into source.


### Line 20–21

```text
 20      with engine.begin() as conn:
 21          for p in sorted(Path(sql_dir).glob('0[0-5]_*.sql')): conn.exec_driver_sql(p.read_text())
```

Start a transaction and execute schema/table SQL files in sorted numeric order. If a later database operation raises, the transaction rolls back.


### Line 22–24

```text
 22          # Dedicated database recommended. One atomic snapshot avoids stale mixed-run rows.
 23          targets=','.join(f'{s}.{t}' for _,s,t in MAPPING)
 24          conn.exec_driver_sql('TRUNCATE '+targets)
```

Truncate all owned target tables together so stale previous-run records cannot mix with new data. This replaces data and requires a dedicated project database; there is no historical snapshot retention.


### Line 25–29

```text
 25          inspector=inspect(conn)
 26          for source,schema,table in MAPPING:
 27              fields={c['name'] for c in inspector.get_columns(table,schema=schema)}
 28              parquet=pq.ParquetFile(Path(out)/(source+'.parquet'))
 29              selected=[n for n in parquet.schema_arrow.names if n in fields]
```

Inspect each target's columns and project only matching Parquet fields. Exports can contain richer analytical attributes than the serving schema.


### Line 30–32

```text
 30              for batch in parquet.iter_batches(batch_size=10000,columns=selected):
 31                  frame=batch.to_pandas()
 32                  frame.to_sql(table,conn,schema=schema,if_exists='append',index=False,chunksize=1000,method=None)
```

Read 10,000-row Parquet batches and insert 1,000-row chunks through the same transaction. This limits transfer-frame memory; ordinary to_sql inserts prioritize portability over the speed of PostgreSQL COPY.


### Line 33

```text
 33          for p in sorted(Path(sql_dir).glob('0[6-8]_*.sql')): conn.exec_driver_sql(p.read_text())
```

After rows exist, create analytical views/indexes and refresh materialized summaries.


### Line 34–35

```text
 34          comments=Path(sql_dir)/'10_document_columns.sql'
 35          if comments.exists(): conn.exec_driver_sql(comments.read_text())
```

Apply human-readable database column comments when the documentation SQL exists.


### Line 36–37

```text
 36          failures=conn.exec_driver_sql((Path(sql_dir)/'09_data_quality_tests.sql').read_text()).fetchall()
 37          if any(n for _,n in failures): raise ValueError(f'SQL quality checks failed: {failures}')
```

Run SQL checks and raise on any nonzero failure count so an invalid snapshot cannot commit.


### Line 38

```text
 38      engine.dispose()
```

Dispose of pooled database connections after successful transaction completion. A try/finally would ensure this cleanup also runs after exceptions.


## src/__init__.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  """Retail Supply Chain Control Tower."""
```

Package marker/docstring: identifies this folder as a Python package and documents its purpose. It does not run an analytical calculation.


## src/forecasting/__init__.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  """Retail Supply Chain Control Tower."""
```

Package marker/docstring: identifies this folder as a Python package and documents its purpose. It does not run an analytical calculation.


## src/ingestion/__init__.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  """Retail Supply Chain Control Tower."""
```

Package marker/docstring: identifies this folder as a Python package and documents its purpose. It does not run an analytical calculation.


## src/inventory/__init__.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  """Retail Supply Chain Control Tower."""
```

Package marker/docstring: identifies this folder as a Python package and documents its purpose. It does not run an analytical calculation.


## src/operations/__init__.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  """Retail Supply Chain Control Tower."""
```

Package marker/docstring: identifies this folder as a Python package and documents its purpose. It does not run an analytical calculation.


## src/transformation/__init__.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  """Retail Supply Chain Control Tower."""
```

Package marker/docstring: identifies this folder as a Python package and documents its purpose. It does not run an analytical calculation.


## src/utils/__init__.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  """Retail Supply Chain Control Tower."""
```

Package marker/docstring: identifies this folder as a Python package and documents its purpose. It does not run an analytical calculation.


## src/validation/__init__.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  """Retail Supply Chain Control Tower."""
```

Package marker/docstring: identifies this folder as a Python package and documents its purpose. It does not run an analytical calculation.


## tests/conftest.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import sys
```

Import sys from sys to provide Python interpreter settings, here the import search path.


### Line 2

```text
  2  from pathlib import Path
```

Import Path from pathlib to provide portable filesystem paths; it avoids hard-coding slash separators and supports repository-relative locations.


### Line 3

```text
  3  sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
```

Put the repository root on Python's import path when pytest starts, allowing tests to import src modules without packaging/installing the project.


## tests/test_data_quality.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 2

```text
  2  import pytest
```

Import pytest from pytest to provide test assertions, parametrized cases, temporary fixtures and expected-error checks.


### Line 3

```text
  3  from src.validation.schema_validation import required_columns,unique_keys
```

Import required_columns, unique_keys from src.validation.schema_validation to provide reuse src/validation/schema_validation.py rather than duplicating that stage’s implementation.


### Line 4

```text
  4  from src.transformation.transform_dataco import transform_dataco
```

Import transform_dataco from src.transformation.transform_dataco to provide reuse src/transformation/transform_dataco.py rather than duplicating that stage’s implementation.


### Line 5

```text
  5  from src.ingestion.load_dataco import load_dataco,ALLOWED
```

Import load_dataco, ALLOWED from src.ingestion.load_dataco to provide reuse src/ingestion/load_dataco.py rather than duplicating that stage’s implementation.


### Line 6

```text
  6  from src.fixtures import create_fixture
```

Import create_fixture from src.fixtures to provide reuse src/fixtures.py rather than duplicating that stage’s implementation.


### Line 7

```text
  7  from src.config import load_config
```

Import load_config from src.config to provide reuse src/config.py rather than duplicating that stage’s implementation.


### Line 8

```text
  8
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 9–10

```text
  9  def test_required_columns():
 10      with pytest.raises(ValueError): required_columns(['a'],['a','b'],'test')
```

Assert that a missing required field raises an error; a silently accepted incomplete schema would fail later or produce wrong calculations.


### Line 11–12

```text
 11  def test_keys():
 12      with pytest.raises(ValueError): unique_keys(pd.DataFrame({'id':[1,1]}),['id'])
```

Assert duplicate business keys are rejected before joins can multiply rows.


### Line 13–15

```text
 13  def test_dataco_grain_and_privacy(tmp_path):
 14      _,dc=create_fixture(tmp_path);cfg=load_config()['dataco']
 15      raw,_=load_dataco(dc/cfg['filename'],cfg,tmp_path)
```

Generate fresh synthetic inputs in pytest's temporary folder and load them through the real ingestion function.


### Line 16

```text
 16      assert set(raw.columns)<=ALLOWED
```

Verify the output column set is a subset of the allowlist; new source fields cannot escape by default.


### Line 17–20

```text
 17      lines,orders=transform_dataco(raw,cfg,tmp_path)
 18      assert len(lines)>len(orders)==240
 19      assert orders.order_id.is_unique
 20      assert orders.late_order.dropna().between(0,1).all()
```

Transform data and verify multiple lines collapse to exactly 240 unique orders with valid binary/nonmissing late outcomes.


### Line 21–22

```text
 21      assert not any('customer_id' in c or 'email' in c or 'password' in c for c in lines)
 22      assert 'PRIVATE_TEST_NAME' not in lines.to_csv(index=False)
```

Check that named customer/credential columns and the test private-name sentinel do not reach profitability output. These are specific privacy checks, not a proof against all possible sensitive text.


### Line 23–24

```text
 23      assert lines.sales.sum()==pytest.approx(raw.order_item_total.sum())
 24      assert lines.profit.sum()==pytest.approx(raw.benefit_per_order.sum())
```

Reconcile line sales/profit with configured raw fixture fields; transformation must not duplicate or lose valid monetary values.


### Line 25–29

```text
 25  def test_conflicting_orders_fail(tmp_path):
 26      _,dc=create_fixture(tmp_path);cfg=load_config()['dataco'];raw,_=load_dataco(dc/cfg['filename'],cfg,tmp_path)
 27      order=raw.order_id.value_counts().idxmax();idx=raw.index[raw.order_id==order][0]
 28      raw.loc[idx,'days_for_shipping_real']=80
 29      with pytest.raises(ValueError,match='conflicting'): transform_dataco(raw,cfg,tmp_path)
```

Deliberately corrupt one line's shipping duration within a multi-line order and require a conflict failure, protecting the one-outcome-per-order assumption.


### Line 30–33

```text
 30  def test_missing_optional_does_not_invent_profit(tmp_path):
 31      _,dc=create_fixture(tmp_path);cfg=load_config()['dataco'];raw,_=load_dataco(dc/cfg['filename'],cfg,tmp_path)
 32      lines,_=transform_dataco(raw.drop(columns=['benefit_per_order']),cfg,tmp_path)
 33      assert lines.profit.isna().all()
```

Remove the profit source and ensure missing profit stays missing rather than being invented as zero or derived from an unrelated field.


## tests/test_forecasting_features.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws.


### Line 2

```text
  2  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 3

```text
  3  import duckdb
```

Import duckdb from duckdb to provide local SQL queries over CSV/Parquet and analytical window calculations.


### Line 4

```text
  4  import pytest
```

Import pytest from pytest to provide test assertions, parametrized cases, temporary fixtures and expected-error checks.


### Line 5

```text
  5  from src.forecasting.feature_engineering import create_feature_view,past_features
```

Import create_feature_view, past_features from src.forecasting.feature_engineering to provide reuse src/forecasting/feature_engineering.py rather than duplicating that stage’s implementation. The imported name(s) past_features are not referenced elsewhere in this module’s executable syntax; they are cleanup opportunities rather than needed logic here.


### Line 6

```text
  6  from src.forecasting.baselines import baseline
```

Import baseline from src.forecasting.baselines to provide reuse src/forecasting/baselines.py rather than duplicating that stage’s implementation.


### Line 7

```text
  7  from src.utils.metrics import rmsse_scale,metrics
```

Import rmsse_scale, metrics from src.utils.metrics to provide reuse src/utils/metrics.py rather than duplicating that stage’s implementation.


### Line 8

```text
  8
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 9–13

```text
  9  def features(values):
 10      n=len(values)
 11      x=pd.DataFrame({'item_id':'a','store_id':'s','date':pd.date_range('2020-01-01',periods=n),'units_sold':values,'revenue':values,'sell_price':1.})
 12      con=duckdb.connect();con.register('sales',x);create_feature_view(con)
 13      result=con.execute('SELECT * FROM features ORDER BY date').df();con.close();return result
```

Create a tiny known daily series in DuckDB, run the production feature builder, and return ordered features. Controlled values make leakage checks interpretable.


### Line 14

```text
 14
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 15–18

```text
 15  def test_future_and_current_perturbation_do_not_change_past_features():
 16      y=np.arange(1.,81.);before=features(y);y[60:]=99999;after=features(y)
 17      cols=['lag_1','lag_7','lag_28','rolling_mean_7','rolling_std_28','days_since_last_sale']
 18      pd.testing.assert_frame_equal(before.loc[:60,cols],after.loc[:60,cols])
```

Replace current/future target values with extreme numbers and confirm earlier/current predictor rows do not change. This tests a behavioral no-leakage property rather than copying the implementation formula.


### Line 19

```text
 19      assert before.loc[60,'rolling_mean_7']==np.mean(np.arange(54.,61.))
```

Check one seven-day mean against a hand-understandable historical slice to detect window-boundary errors.


### Line 20–21

```text
 20  def test_series_seasonal_pattern():
 21      assert baseline([1,2,3,4,5,6,7],10,'seasonal_7').tolist()==[1,2,3,4,5,6,7,1,2,3]
```

Verify the weekly baseline repeats the intended sequence beyond one full week.


### Line 22–25

```text
 22  def test_metrics_zero_handling_and_scale():
 23      assert np.isnan(metrics([0,0],[1,1])['wape'])
 24      assert rmsse_scale([0,0,1,2,4])==pytest.approx(2.5)
 25      assert np.isnan(rmsse_scale([1,1,1]))
```

Verify zero-demand WAPE is undefined, leading zeros are removed for RMSSE scale, and constant history has undefined scale.


### Line 26

```text
 26
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 27–31

```text
 27  def test_recursive_predictions_ignore_heldout_actuals():
 28      from src.config import ROOT,load_config
 29      from src.forecasting.train_models import train_global
 30      from src.forecasting.generate_forecasts import predict_origin
 31      from src.ingestion.load_m5 import load_m5
```

Set up the recursive forecast regression test using actual project helpers. load_m5 is imported but unused in this test.


### Line 32–36

```text
 32      x=pd.read_parquet(ROOT/'data/powerbi/fixture/sales_daily.parquet')
 33      x=x[x.item_id==x.item_id.iloc[0]].copy()
 34      con=duckdb.connect();con.register('input_sales',x);con.execute('CREATE TABLE sales AS SELECT * FROM input_sales')
 35      cal=pd.read_csv(ROOT/'data/sample/m5/calendar.csv');con.register('calendar',cal)
 36      create_feature_view(con);origin=x.date.max()-pd.Timedelta(days=28);cfg=load_config()
```

Read previously generated fixture sales, narrow to one product, create an editable SQL table/calendar and choose a held-out origin. This test depends on running the demo first.


### Line 37–38

```text
 37      m,levels,_=train_global(con,origin,cfg)
 38      a=predict_origin(con,origin,7,['lightgbm'],cfg,m,levels)
```

Train once and forecast seven days using the unmodified stored data.


### Line 39–41

```text
 39      con.execute('UPDATE sales SET units_sold=units_sold+10000 WHERE date>?',[origin])
 40      b=predict_origin(con,origin,7,['lightgbm'],cfg,m,levels)
 41      pd.testing.assert_frame_equal(a,b);con.close()
```

Change held-out sales dramatically and recompute using the same fitted model; require identical forecasts. The test proves that this path does not read those held-out actuals into recursive features.


## tests/test_inventory_formulas.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  import math
```

Import math from math to provide scalar square roots and upward quantity rounding.


### Line 2

```text
  2  import numpy as np
```

Import numpy as np from numpy to provide numerical arrays, vectorized arithmetic and reproducible pseudo-random draws.


### Line 3

```text
  3  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 4

```text
  4  import pytest
```

Import pytest from pytest to provide test assertions, parametrized cases, temporary fixtures and expected-error checks.


### Line 5

```text
  5  from statistics import NormalDist
```

Import NormalDist from statistics to provide the normal-distribution quantile/CDF used by the inventory approximation.


### Line 6

```text
  6  from src.inventory.calculate_inventory_policy import safety_stock,eoq,round_order,policies
```

Import safety_stock, eoq, round_order, policies from src.inventory.calculate_inventory_policy to provide reuse src/inventory/calculate_inventory_policy.py rather than duplicating that stage’s implementation. The imported name(s) policies are not referenced elsewhere in this module’s executable syntax; they are cleanup opportunities rather than needed logic here.


### Line 7

```text
  7  from src.inventory.inventory_simulation import simulate_series,summarize
```

Import simulate_series, summarize from src.inventory.inventory_simulation to provide reuse src/inventory/inventory_simulation.py rather than duplicating that stage’s implementation.


### Line 8

```text
  8
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 9–10

```text
  9  def test_safety_stock():
 10      assert safety_stock(10,3,7,2,.95)==pytest.approx(NormalDist().inv_cdf(.95)*math.sqrt(7*9+100*4))
```

Check safety-stock arithmetic against a specified example. This validates implementation of the chosen formula, not whether its assumptions fit real demand.


### Line 11–13

```text
 11  @pytest.mark.parametrize('level',[0,1,-.1,1.1])
 12  def test_service_guard(level):
 13      with pytest.raises(ValueError): safety_stock(10,3,7,2,level)
```

Parametrize four invalid service probabilities and require errors. One function creates four test cases, explaining why test counts exceed function counts.


### Line 14–17

```text
 14  def test_eoq_and_rounding():
 15      assert eoq(1200,25,3)==pytest.approx(math.sqrt(20000))
 16      assert round_order(7,6,6)==12
 17      assert round_order(0,6,6)==0
```

Check EOQ arithmetic, rounding 7 units up to a 12-unit case multiple, and the no-order behavior for zero need.


### Line 18

```text
 18
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 19–22

```text
 19  def test_balance_arrivals_and_fill():
 20      p=dict(item_id='a',store_id='s',initial_inventory=10,average_lead_time_days=2,lead_time_standard_deviation=0,
 21       review_period_days=1,average_daily_demand=5,minimum_order_quantity=6,case_pack_size=6,protection_safety_stock=4,
 22       eoq=12,estimated_unit_cost=2,annual_holding_cost_rate=.25,ordering_cost_per_order=10,lost_sale_penalty=3,last_price=4,target_service_level=.95)
```

Construct a simple deterministic inventory scenario with a two-day lead time, known daily demand and defined costs/lot sizes.


### Line 23

```text
 23      x=simulate_series(np.repeat(5,10),np.repeat(5,10),pd.date_range('2020-01-01',periods=10),p,'baseline',42,0)
```

Replay the baseline for ten days so arrivals, purchases and shortages have a predictable structure.


### Line 24–25

```text
 24      np.testing.assert_allclose(x.opening_inventory+x.arrivals-x.fulfilled_units,x.closing_inventory)
 25      np.testing.assert_allclose(x.actual_demand,x.fulfilled_units+x.lost_sales_units)
```

Check conservation identities: opening + arrivals − fulfilled = closing, and actual demand = fulfilled + lost. These catch deep accounting mistakes independently of policy quality.


### Line 26

```text
 26      assert x.arrivals.iloc[0]==x.arrivals.iloc[1]==0
```

Assert no order can arrive on either of the first two days with a two-day lead time and no opening pipeline.


### Line 27–28

```text
 27      assert (x.order_quantity%6==0).all()
 28      k=summarize(x);assert k.fill_rate.between(0,1).all()
```

Verify case-pack multiples and feasible fill-rate bounds after summarization.


## tests/test_pipeline.py

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  from pathlib import Path
```

Import Path from pathlib to provide portable filesystem paths; it avoids hard-coding slash separators and supports repository-relative locations. The imported name(s) Path are not referenced elsewhere in this module’s executable syntax; they are cleanup opportunities rather than needed logic here.


### Line 2

```text
  2  import json
```

Import json from json to provide readable structured audit/config/result records. The imported name(s) json are not referenced elsewhere in this module’s executable syntax; they are cleanup opportunities rather than needed logic here.


### Line 3

```text
  3  import os
```

Import os from os to provide environment variables, here database configuration.


### Line 4

```text
  4  import pandas as pd
```

Import pandas as pd from pandas to provide labeled tabular data, joins/grouping and date handling.


### Line 5

```text
  5  import pytest
```

Import pytest from pytest to provide test assertions, parametrized cases, temporary fixtures and expected-error checks.


### Line 6

```text
  6  from src.config import ROOT,load_config
```

Import ROOT, load_config from src.config to provide reuse src/config.py rather than duplicating that stage’s implementation. The imported name(s) load_config are not referenced elsewhere in this module’s executable syntax; they are cleanup opportunities rather than needed logic here.


### Line 7

```text
  7  from src.ingestion.load_m5 import detect_sales
```

Import detect_sales from src.ingestion.load_m5 to provide reuse src/ingestion/load_m5.py rather than duplicating that stage’s implementation.


### Line 8

```text
  8
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 9

```text
  9  REQUIRED=['sales_daily','sales_monthly','product_store_performance','demand_forecasts_28d','forecast_model_metrics','forecast_accuracy_by_segment','inventory_assumptions','inventory_policy_recommendations','inventory_simulation_daily','inventory_simulation_kpis','abc_xyz_segmentation','stockout_risk','excess_inventory','dataco_delivery_performance','dataco_shipping_mode_performance','dataco_profitability','executive_kpis']
```

List essential expected outputs as an integration contract. It is a selected inventory, not a check of every possible optional export.


### Line 10

```text
 10
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 11–13

```text
 11  def test_sales_file_precedence(tmp_path):
 12      (tmp_path/'sales_train_validation.csv').touch();assert 'validation' in detect_sales(tmp_path).name
 13      (tmp_path/'sales_train_evaluation.csv').touch();assert 'evaluation' in detect_sales(tmp_path).name
```

Create empty named files and verify evaluation-file precedence with validation fallback. The test covers file selection, not CSV contents.


### Line 14

```text
 14
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 15–18

```text
 15  def test_executed_fixture_outputs():
 16      out=ROOT/'data/powerbi/fixture'
 17      assert out.exists(),'Run make demo before integration tests'
 18      for name in REQUIRED: assert (out/(name+'.parquet')).exists(),name
```

Require an executed fixture folder and all essential Parquet outputs. This is why running pytest alone in a fresh clone is insufficient.


### Line 19–22

```text
 19      f=pd.read_parquet(out/'demand_forecasts_28d.parquet')
 20      assert f.groupby(['item_id','store_id']).size().eq(28).all()
 21      assert (f.date-f.origin).dt.days.equals(f.horizon)
 22      assert f.forecast_units.ge(0).all()
```

Require exactly 28 forecasts per pair, aligned date/origin/horizon and nonnegative units.


### Line 23

```text
 23      assert (f.lower_95<=f.lower_80).all() and (f.upper_95>=f.upper_80).all()
```

Check interval nesting: the 95% band must contain the 80% band. This verifies structure, not statistical coverage.


### Line 24–27

```text
 24      s=pd.read_parquet(out/'sales_daily.parquet');p=pd.read_parquet(out/'dim_product.parquet');d=pd.read_parquet(out/'dim_date.parquet')
 25      assert p.item_id.is_unique and d.date_key.is_unique
 26      assert set(s.item_id)<=set(p.item_id) and set(f.date_key)<=set(d.date_key)
 27      assert s.units_sold.ge(0).all() and s.sell_price.dropna().ge(0).all()
```

Check dimension uniqueness, referenced product/date membership and nonnegative observed quantities/prices.


### Line 28–29

```text
 28      inv=pd.read_parquet(out/'inventory_policy_recommendations.parquet')
 29      assert ((inv.reorder_point-inv.expected_lead_time_demand-inv.safety_stock).abs()<1e-8).all()
```

Reconcile reorder point with expected lead-time demand plus safety stock to catch output/formula inconsistency.


### Line 30–33

```text
 30      for path in out.glob('*.parquet'):
 31          import pyarrow.parquet as pq
 32          cols=pq.read_schema(path).names
 33          assert not any(c in cols for c in ['customer_email','customer_password','customer_fname','customer_id','customer_street','phone'])
```

Inspect every Parquet schema for specifically forbidden sensitive column names. This does not scan every cell for private content.


### Line 34

```text
 34
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 35–36

```text
 35  def test_postgres_integration():
 36      if not os.getenv('TEST_DATABASE_URL'): pytest.skip('Set TEST_DATABASE_URL for a dedicated disposable PostgreSQL database')
```

Skip database integration unless TEST_DATABASE_URL is explicitly provided for a disposable database. This is the skipped test in your 18-passed/1-skipped result, if the checked source version matches your run.


### Line 37–39

```text
 37      from src.database import load_database
 38      os.environ['DATABASE_URL']=os.environ['TEST_DATABASE_URL']
 39      load_database(ROOT/'data/powerbi/fixture',ROOT/'sql')
```

Point the loader at that disposable database and execute the real transactional load, whose SQL checks must also pass. This can replace that database's project tables.


## sql/00_create_schemas.sql

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  CREATE SCHEMA IF NOT EXISTS common;
```

Create shared calendar namespace if absent; schemas organize tables and avoid name collisions.


### Line 2

```text
  2  CREATE SCHEMA IF NOT EXISTS m5;
```

Create the M5 namespace for retail/forecast/simulated inventory data.


### Line 3

```text
  3  CREATE SCHEMA IF NOT EXISTS dataco;
```

Create an independent DataCo namespace for logistics/profit data.


### Line 4

```text
  4  CREATE SCHEMA IF NOT EXISTS mart;
```

Create a mart namespace for reusable business-facing views.


### Line 5–6

```text
  5  COMMENT ON SCHEMA m5 IS 'M5 retail sales and simulated inventory. No DataCo transactions.';
  6  COMMENT ON SCHEMA dataco IS 'Independent DataCo operational domain; customer PII excluded.';
```

Store domain boundaries/privacy notes in database metadata so SQL users can see them without reading Python.


## sql/01_create_dimensions.sql

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1–2

```text
  1  CREATE TABLE IF NOT EXISTS common.dim_date (
  2   date_key integer PRIMARY KEY, date date NOT NULL UNIQUE, year integer NOT NULL, month integer CHECK(month BETWEEN 1 AND 12), quarter integer CHECK(quarter BETWEEN 1 AND 4));
```

Create a unique date dimension with primary key and basic month/quarter bounds. NOT NULL is explicit for core fields; a CHECK by itself generally permits SQL NULL.


### Line 3–4

```text
  3  CREATE TABLE IF NOT EXISTS m5.dim_state (state_id text PRIMARY KEY);
  4  CREATE TABLE IF NOT EXISTS m5.dim_category (category_id text PRIMARY KEY);
```

Create single-key state/category lookups as parents for dependent dimensions.


### Line 5–7

```text
  5  CREATE TABLE IF NOT EXISTS m5.dim_department (department_id text PRIMARY KEY, category_id text NOT NULL REFERENCES m5.dim_category);
  6  CREATE TABLE IF NOT EXISTS m5.dim_store (store_id text PRIMARY KEY,state_id text NOT NULL REFERENCES m5.dim_state);
  7  CREATE TABLE IF NOT EXISTS m5.dim_product (item_id text PRIMARY KEY,department_id text NOT NULL REFERENCES m5.dim_department,category_id text NOT NULL REFERENCES m5.dim_category);
```

Create department/store/product hierarchies with foreign keys. This rejects a product referencing a nonexistent category/department; it does not independently prove all hierarchy combinations agree.


### Line 8

```text
  8  CREATE TABLE IF NOT EXISTS m5.dim_event (event_name text PRIMARY KEY,event_type text);
```

Use event_name as an event key, assuming one type per name; changes to that assumption require a richer event key.


### Line 9

```text
  9  CREATE TABLE IF NOT EXISTS m5.bridge_date_event (date_key integer REFERENCES common.dim_date,event_name text REFERENCES m5.dim_event,PRIMARY KEY(date_key,event_name));
```

Use a composite date/event bridge key so two events on the same day do not require two sales rows.


### Line 10

```text
 10  CREATE TABLE IF NOT EXISTS dataco.dim_order_date (date_key integer PRIMARY KEY REFERENCES common.dim_date,date date UNIQUE NOT NULL,year integer,month integer,quarter integer);
```

Create DataCo's own order-date role linked to the shared calendar values. The BI relationship model can keep domain date filters separate.


### Line 11–15

```text
 11  CREATE TABLE IF NOT EXISTS dataco.dim_product_category (category text PRIMARY KEY);
 12  CREATE TABLE IF NOT EXISTS dataco.dim_market (market text PRIMARY KEY);
 13  CREATE TABLE IF NOT EXISTS dataco.dim_region (region text PRIMARY KEY);
 14  CREATE TABLE IF NOT EXISTS dataco.dim_shipping_mode (shipping_mode text PRIMARY KEY);
 15  CREATE TABLE IF NOT EXISTS dataco.dim_customer_segment (customer_segment text PRIMARY KEY);
```

Create domain-specific DataCo categorical lookup tables rather than treating similar M5 labels as matching entities.


### Line 16

```text
 16  COMMENT ON TABLE m5.bridge_date_event IS 'Supports both M5 calendar events on the same date; avoid fan-out of sales.';
```

Document that directly joining the multi-event bridge to sales and summing unadjusted rows can cause fan-out/double counting.


## sql/02_create_m5_facts.sql

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1–2

```text
  1  CREATE TABLE IF NOT EXISTS m5.fact_sales_daily (
  2   item_id text REFERENCES m5.dim_product,store_id text REFERENCES m5.dim_store,date_key integer REFERENCES common.dim_date,
```

Create daily sales facts keyed to valid product, store and date dimensions.


### Line 3–4

```text
  3   date date NOT NULL,units_sold double precision NOT NULL CHECK(units_sold>=0),sell_price double precision CHECK(sell_price>=0),revenue double precision,
  4   wm_yr_wk integer,snap_flag integer CHECK(snap_flag IN (0,1)),event_flag integer CHECK(event_flag IN (0,1)),
```

Store observed units, weekly price, derived revenue and flags with basic nonnegative/binary checks. Revenue is not checked against units×price at database level here.


### Line 5

```text
  5   PRIMARY KEY(item_id,store_id,date_key));
```

Enforce one row per item-store-day with a composite primary key.


### Line 6–7

```text
  6  CREATE TABLE IF NOT EXISTS m5.fact_sell_price (
  7   item_id text REFERENCES m5.dim_product,store_id text REFERENCES m5.dim_store,wm_yr_wk integer,sell_price double precision CHECK(sell_price>=0),PRIMARY KEY(item_id,store_id,wm_yr_wk));
```

Keep a separate weekly price fact at item/store/week grain. Storing daily facts and weekly prices separately avoids pretending prices are independently observed each day.


### Line 8–9

```text
  8  COMMENT ON COLUMN m5.fact_sales_daily.revenue IS 'Recorded units times listed weekly price; not accounting net revenue.';
  9  COMMENT ON COLUMN m5.fact_sales_daily.units_sold IS 'Recorded sales, possibly censored by unobserved availability.';
```

Document revenue as a listed-price proxy and sales as possibly constrained by unavailable stock. These limitations affect all downstream interpretations.


## sql/03_create_dataco_facts.sql

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1–2

```text
  1  CREATE TABLE IF NOT EXISTS dataco.fact_delivery_performance (
  2   order_id bigint PRIMARY KEY, date_key integer REFERENCES dataco.dim_order_date,order_date date,
```

Create a delivery fact whose primary key is order_id, ensuring every counted delivery is an order rather than an order line.


### Line 3–6

```text
  3   shipping_mode text REFERENCES dataco.dim_shipping_mode,market text REFERENCES dataco.dim_market,
  4   region text REFERENCES dataco.dim_region,customer_segment text REFERENCES dataco.dim_customer_segment,
  5   actual_shipping_days double precision,scheduled_shipping_days double precision,
  6   delivery_eligible boolean NOT NULL,late_order integer CHECK(late_order IN(0,1)),delay_days double precision,positive_delay_days double precision);
```

Store shipment dimensions, actual/promise durations, explicit eligibility and nullable late/delay measures. NULL can mean ineligible/unknown; it must not become on-time automatically.


### Line 7–9

```text
  7  CREATE TABLE IF NOT EXISTS dataco.fact_orders (
  8   order_item_id bigint PRIMARY KEY,order_id bigint NOT NULL REFERENCES dataco.fact_delivery_performance,
  9   date_key integer REFERENCES dataco.dim_order_date,order_date date,
```

Create the order-line fact with order_item_id as key and a foreign key to its delivery order and order-date dimension.


### Line 10–13

```text
 10   category text REFERENCES dataco.dim_product_category,market text REFERENCES dataco.dim_market,
 11   region text REFERENCES dataco.dim_region,shipping_mode text REFERENCES dataco.dim_shipping_mode,
 12   customer_segment text REFERENCES dataco.dim_customer_segment,product_name text,quantity double precision,
 13   sales double precision,profit double precision,invalid_sales_flag boolean,abnormal_profit_flag boolean);
```

Attach line descriptions, quantity, configured money values and quality flags. Several fields are nullable to preserve missingness rather than fabricate values.


### Line 14–15

```text
 14  CREATE TABLE IF NOT EXISTS dataco.fact_profitability (
 15   order_item_id bigint PRIMARY KEY REFERENCES dataco.fact_orders,sales double precision,profit double precision,profit_margin double precision,loss_making_line boolean);
```

Create a one-to-one profitability extension keyed to the order line. Because monetary fields are also present in fact_orders, consumers must avoid adding the two representations together.


### Line 16–18

```text
 16  COMMENT ON TABLE dataco.fact_orders IS 'One row per order item, not one per order. Order IDs legitimately repeat.';
 17  COMMENT ON TABLE dataco.fact_profitability IS 'Line-level configured source sales and benefit. Never sum repeated order total columns.';
 18  COMMENT ON COLUMN dataco.fact_delivery_performance.late_order IS 'Derived actual duration > promise. Null for ineligible or absent durations.';
```

Persist grain and money/outcome semantics as metadata. Repeated order IDs across lines are valid; repeated order-level totals would not be safe to sum as line profit.


## sql/04_create_forecast_tables.sql

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1–3

```text
  1  CREATE TABLE IF NOT EXISTS m5.fact_forecast (
  2   item_id text REFERENCES m5.dim_product,store_id text REFERENCES m5.dim_store,date_key integer REFERENCES common.dim_date,
  3   origin date NOT NULL,date date NOT NULL,horizon integer CHECK(horizon BETWEEN 1 AND 28),model text,
```

Create future forecast facts with entity/date keys, explicit origin and a 1–28 production horizon constraint.


### Line 4–5

```text
  4   forecast_units double precision CHECK(forecast_units>=0),lower_80 double precision,upper_80 double precision,lower_95 double precision,upper_95 double precision,
  5   PRIMARY KEY(item_id,store_id,origin,date_key,model),CHECK(date>origin));
```

Store point and interval values, disallow negative point demand and require target dates after origin. Composite identity includes model and origin so separate forecast versions are distinguishable.


### Line 6–9

```text
  6  CREATE TABLE IF NOT EXISTS m5.fact_forecast_accuracy (
  7   item_id text REFERENCES m5.dim_product,store_id text REFERENCES m5.dim_store,date_key integer REFERENCES common.dim_date,
  8   origin date,date date,model text,fold integer,split_role text,actual_units double precision,forecast_units double precision,error double precision,absolute_error double precision,scale double precision,
  9   PRIMARY KEY(item_id,store_id,origin,date_key,model));
```

Create backtest facts with actuals, predictions, fold role, signed/absolute errors and training scale. The same target date can validly occur for different origins/models, so those enter the key.


### Line 10–11

```text
 10  COMMENT ON COLUMN m5.fact_forecast_accuracy.error IS 'Forecast minus actual; positive means overforecast.';
 11  COMMENT ON COLUMN m5.fact_forecast.lower_95 IS 'Empirical residual interval, approximate coverage, clipped at zero.';
```

Document error sign and approximate/clipped interval interpretation to prevent dashboard label mistakes.


## sql/05_create_inventory_tables.sql

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1–2

```text
  1  CREATE TABLE IF NOT EXISTS m5.fact_inventory_policy (
  2   item_id text REFERENCES m5.dim_product,store_id text REFERENCES m5.dim_store,as_of_date date,target_service_level double precision CHECK(target_service_level>0 AND target_service_level<1),
```

Create policy facts with pair, as-of date and valid service probability. A service target identifies an alternative scenario.


### Line 3–6

```text
  3   average_daily_demand double precision,forecast_daily_demand double precision,initial_inventory double precision,
  4   estimated_unit_cost double precision,safety_stock double precision,reorder_point double precision,eoq double precision,
  5   days_of_supply double precision,inventory_value double precision,stockout_probability double precision CHECK(stockout_probability BETWEEN 0 AND 1),
  6   recommended_order_quantity double precision CHECK(recommended_order_quantity>=0),excess_units double precision,excess_value double precision,
```

Store forecast/demand inputs, assumed stock/cost, policy quantities, investment and modeled risk/excess. Only selected basic ranges are enforced here, not every formula identity.


### Line 7

```text
  7   PRIMARY KEY(item_id,store_id,as_of_date,target_service_level));
```

Use pair/date/service as the key so three target levels produce three valid alternatives rather than duplicate records.


### Line 8–14

```text
  8  CREATE TABLE IF NOT EXISTS m5.fact_inventory_simulation (
  9   item_id text REFERENCES m5.dim_product,store_id text REFERENCES m5.dim_store,date date,policy text,scenario text,run_id integer,target_service_level double precision,
 10   opening_inventory double precision,arrivals double precision,actual_demand double precision,forecast_demand double precision,
 11   fulfilled_units double precision,lost_sales_units double precision,order_quantity double precision,in_transit_units double precision,closing_inventory double precision,
 12   stockout_event integer,holding_cost double precision,ordering_cost double precision,lost_sale_cost double precision,total_inventory_cost double precision,lost_sales_value double precision,
 13   estimated_unit_cost double precision,completed_cycles integer,successful_cycles integer,
 14   PRIMARY KEY(item_id,store_id,date,policy,scenario,run_id,target_service_level),
```

Create the daily simulation ledger keyed by pair/date/policy/scenario/run/service. These dimensions must be preserved to avoid adding mutually exclusive simulated worlds.


### Line 15–16

```text
 15   CHECK(abs(opening_inventory+arrivals-fulfilled_units-closing_inventory)<0.00001),
 16   CHECK(abs(actual_demand-fulfilled_units-lost_sales_units)<0.00001),CHECK(closing_inventory>=0),CHECK(fulfilled_units>=0));
```

Enforce inventory conservation, demand decomposition and nonnegative stock/fulfillment with a small numerical tolerance for floating-point arithmetic.


### Line 17–18

```text
 17  COMMENT ON TABLE m5.fact_inventory_policy IS 'Scenario recommendations based on simulated inputs. Select one as-of date and service level.';
 18  COMMENT ON TABLE m5.fact_inventory_simulation IS 'Daily lost-sales scenario. Average across Monte Carlo runs; do not sum repeated scenarios.';
```

Document that policy data are assumptions-based snapshots and repeated Monte Carlo runs must be averaged, not counted as additional business activity.


## sql/06_create_analytical_views.sql

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1–3

```text
  1  CREATE OR REPLACE VIEW mart.mart_sales_performance AS
  2   SELECT date_trunc('month',f.date)::date AS month,p.category_id,s.state_id,f.store_id,sum(f.units_sold) units_sold,sum(f.revenue) revenue
  3   FROM m5.fact_sales_daily f JOIN m5.dim_product p USING(item_id) JOIN m5.dim_store s USING(store_id) GROUP BY 1,2,3,4;
```

Aggregate M5 sales by month/category/state/store through many-to-one dimensions, defining a reusable serving view.


### Line 4

```text
  4  CREATE OR REPLACE VIEW mart.mart_demand_forecast AS SELECT * FROM m5.fact_forecast;
```

Expose future forecast facts through a stable mart name; this view does not itself select an origin/model.


### Line 5

```text
  5  CREATE OR REPLACE VIEW mart.mart_forecast_accuracy AS SELECT model,split_role,store_id,sum(absolute_error)/nullif(sum(actual_units),0) wape,sum(error)/nullif(sum(actual_units),0) bias FROM m5.fact_forecast_accuracy GROUP BY 1,2,3;
```

Compute WAPE and bias as ratios of summed errors/actuals by model/role/store; averaging row or subgroup percentages would give different weighting.


### Line 6

```text
  6  CREATE OR REPLACE VIEW mart.mart_inventory_health AS SELECT * FROM m5.fact_inventory_policy;
```

Expose inventory policy snapshots without deleting scenario dimensions.


### Line 7

```text
  7  CREATE OR REPLACE VIEW mart.mart_stockout_risk AS SELECT * FROM m5.fact_inventory_policy WHERE stockout_probability>1-target_service_level;
```

Select policy rows whose modeled stockout probability exceeds the tolerated 1−service risk. This is a modeled screening rule.


### Line 8

```text
  8  CREATE OR REPLACE VIEW mart.mart_product_store_performance AS SELECT item_id,store_id,sum(revenue) revenue,sum(units_sold) units_sold,avg(units_sold) mean_units,stddev_samp(units_sold)/nullif(avg(units_sold),0) demand_cv FROM m5.fact_sales_daily GROUP BY 1,2;
```

Summarize item-store history and CV over the entire loaded period. Unlike Python history_summary, this view is not restricted to 90 days.


### Line 9

```text
  9  CREATE OR REPLACE VIEW mart.mart_delivery_performance AS SELECT * FROM dataco.fact_delivery_performance;
```

Expose the one-row-per-order delivery table for consistent operational denominators.


### Line 10

```text
 10  CREATE OR REPLACE VIEW mart.mart_shipping_mode_performance AS SELECT shipping_mode,count(*) FILTER(WHERE delivery_eligible) eligible_orders,sum(late_order) late_orders,avg(late_order::numeric) late_delivery_rate,avg(positive_delay_days) average_delay_days FROM dataco.fact_delivery_performance GROUP BY 1;
```

Summarize eligible and late orders and delays by mode. avg ignores NULL ineligible outcomes under the transformation contract.


### Line 11

```text
 11  CREATE OR REPLACE VIEW mart.mart_profitability AS SELECT o.category,o.market,o.region,sum(p.sales) sales,sum(p.profit) profit,sum(p.profit)/nullif(sum(p.sales),0) profit_margin FROM dataco.fact_orders o JOIN dataco.fact_profitability p USING(order_item_id) WHERE NOT o.invalid_sales_flag GROUP BY 1,2,3;
```

Join each line to its one-to-one profit extension, exclude flagged invalid sales and use ratio-of-sums margin.


### Line 12–16

```text
 12  CREATE OR REPLACE VIEW mart.mart_executive_kpis AS
 13   SELECT 'M5'::text domain,'historical_revenue'::text metric,sum(revenue) value FROM m5.fact_sales_daily
 14   UNION ALL SELECT 'M5','forecast_units',sum(forecast_units) FROM m5.fact_forecast
 15   UNION ALL SELECT 'DataCo','late_delivery_rate',avg(late_order::double precision) FROM dataco.fact_delivery_performance WHERE delivery_eligible
 16   UNION ALL SELECT 'DataCo','profit',sum(profit) FROM dataco.fact_orders WHERE NOT invalid_sales_flag;
```

Stack separate M5 and DataCo metrics with domain labels using UNION ALL. These rows are independent cards, not quantities to sum into a combined financial total.


### Line 17

```text
 17  COMMENT ON VIEW mart.mart_executive_kpis IS 'Independent domains stacked as labels; no cross-domain transaction joins or combined profit.';
```

Persist the no-cross-domain-join rule as view documentation.


## sql/07_create_materialized_views.sql

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  CREATE MATERIALIZED VIEW IF NOT EXISTS mart.mv_monthly_sales AS SELECT * FROM mart.mart_sales_performance WITH NO DATA;
```

Define a stored monthly summary initially without populated data. Unlike a normal view, materialized results require refresh after source changes.


### Line 2

```text
  2  CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_monthly_sales ON mart.mv_monthly_sales(month,category_id,state_id,store_id);
```

Add a unique key index on the summary grain. This supports stable row identity and can support future concurrent refresh arrangements.


### Line 3–4

```text
  3  -- First refresh must be non-concurrent; subsequent production refreshes can be concurrent.
  4  REFRESH MATERIALIZED VIEW mart.mv_monthly_sales;
```

Populate/refresh using a regular refresh inside the loader. The current implementation does not schedule automatic refreshes or use concurrent refresh.


## sql/08_indexes.sql

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  CREATE INDEX IF NOT EXISTS ix_sales_date_store ON m5.fact_sales_daily(date_key,store_id) INCLUDE(revenue,units_sold);
```

Add a date/store lookup index including revenue/units for common filtered summaries. Potential read gains trade off against index storage and load work.


### Line 2

```text
  2  CREATE INDEX IF NOT EXISTS ix_sales_date_brin ON m5.fact_sales_daily USING brin(date);
```

Add a compact BRIN date index, most useful when physical row order correlates with dates; this assumption should be checked with actual query plans.


### Line 3

```text
  3  CREATE INDEX IF NOT EXISTS ix_orders_order ON dataco.fact_orders(order_id);
```

Index order-line order_id for order aggregation/joins; a line primary key alone does not accelerate lookup by parent order equally well.


### Line 4

```text
  4  CREATE INDEX IF NOT EXISTS ix_orders_category_date ON dataco.fact_orders(category,date_key);
```

Index category/date for category-period profitability filtering.


### Line 5

```text
  5  CREATE INDEX IF NOT EXISTS ix_delivery_late ON dataco.fact_delivery_performance(shipping_mode,order_date) WHERE late_order=1;
```

Create a smaller partial delivery index containing late orders only, aimed at exception investigations.


### Line 6

```text
  6  CREATE INDEX IF NOT EXISTS ix_forecast_origin ON m5.fact_forecast(origin,date_key);
```

Index forecast origin/date to speed version/date selection.


### Line 7–8

```text
  7  ANALYZE m5.fact_sales_daily;
  8  ANALYZE dataco.fact_orders;
```

Refresh planner statistics after loading large fact tables. Index existence does not guarantee the optimizer will choose it or that a query is faster.


## sql/09_data_quality_tests.sql

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  -- Every returned failure count must equal zero. Foreign keys additionally enforce integrity at load time.
```

Define a query contract: each output row is a check name plus violation count, and every count must be zero.


### Line 2–3

```text
  2  SELECT 'negative_sales_units' test,count(*) failures FROM m5.fact_sales_daily WHERE units_sold<0
  3  UNION ALL SELECT 'negative_prices',count(*) FROM m5.fact_sell_price WHERE sell_price<0
```

Count negative quantities/prices as forbidden source values; constraints also protect many of these cases.


### Line 4–5

```text
  4  UNION ALL SELECT 'sales_orphan_product',count(*) FROM m5.fact_sales_daily s LEFT JOIN m5.dim_product p USING(item_id) WHERE p.item_id IS NULL
  5  UNION ALL SELECT 'sales_orphan_date',count(*) FROM m5.fact_sales_daily s LEFT JOIN common.dim_date d USING(date_key) WHERE d.date_key IS NULL
```

Use left joins to detect sales references lacking product/date dimensions.


### Line 6

```text
  6  UNION ALL SELECT 'sales_date_key_mismatch',count(*) FROM m5.fact_sales_daily s JOIN common.dim_date d USING(date_key) WHERE s.date<>d.date
```

Verify the stored sales date equals the date represented by its date_key.


### Line 7

```text
  7  UNION ALL SELECT 'forecast_alignment',count(*) FROM m5.fact_forecast WHERE date-origin<>horizon OR forecast_units<0
```

Require future forecast date minus origin to match horizon and reject negative forecast units.


### Line 8

```text
  8  UNION ALL SELECT 'invalid_intervals',count(*) FROM m5.fact_forecast WHERE lower_95>lower_80 OR lower_80>forecast_units OR upper_80<forecast_units OR upper_95<upper_80
```

Check nested intervals and point containment; these checks cannot verify nominal statistical coverage.


### Line 9

```text
  9  UNION ALL SELECT 'invalid_service',count(*) FROM m5.fact_inventory_policy WHERE target_service_level<=0 OR target_service_level>=1
```

Check service targets stay strictly between zero and one.


### Line 10–11

```text
 10  UNION ALL SELECT 'inventory_balance',count(*) FROM m5.fact_inventory_simulation WHERE abs(opening_inventory+arrivals-fulfilled_units-closing_inventory)>0.00001
 11  UNION ALL SELECT 'invalid_fulfillment',count(*) FROM m5.fact_inventory_simulation WHERE fulfilled_units>actual_demand OR fulfilled_units<0
```

Recheck daily inventory conservation and feasible fulfillment in the serving database.


### Line 12

```text
 12  UNION ALL SELECT 'invalid_late_rate',count(*) FROM mart.mart_shipping_mode_performance WHERE late_delivery_rate NOT BETWEEN 0 AND 1
```

Check aggregated late rates remain between zero and one. NULL/undefined rates are not failures under this predicate.


### Line 13

```text
 13  UNION ALL SELECT 'pii_columns',count(*) FROM information_schema.columns WHERE table_schema IN ('m5','dataco','mart') AND column_name ~ '(email|password|phone|street|customer_fname|customer_lname|customer_id)';
```

Inspect schema column names for listed private-field patterns. This is a naming safeguard rather than a scan of every value for sensitive content.


## sql/10_document_columns.sql

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  COMMENT ON TABLE common.dim_date IS 'Natural-key dimension: date. Independent source-domain meanings apply.';
```

Store documentation on table common.dim_date: “Natural-key dimension: date. Independent source-domain meanings apply.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 2

```text
  2  COMMENT ON TABLE dataco.dim_customer_segment IS 'Natural-key dimension: customer segment. Independent source-domain meanings apply.';
```

Store documentation on table dataco.dim_customer_segment: “Natural-key dimension: customer segment. Independent source-domain meanings apply.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 3

```text
  3  COMMENT ON TABLE dataco.dim_market IS 'Natural-key dimension: market. Independent source-domain meanings apply.';
```

Store documentation on table dataco.dim_market: “Natural-key dimension: market. Independent source-domain meanings apply.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 4

```text
  4  COMMENT ON TABLE dataco.dim_order_date IS 'Natural-key dimension: order date. Independent source-domain meanings apply.';
```

Store documentation on table dataco.dim_order_date: “Natural-key dimension: order date. Independent source-domain meanings apply.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 5

```text
  5  COMMENT ON TABLE dataco.dim_product_category IS 'Natural-key dimension: product category. Independent source-domain meanings apply.';
```

Store documentation on table dataco.dim_product_category: “Natural-key dimension: product category. Independent source-domain meanings apply.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 6

```text
  6  COMMENT ON TABLE dataco.dim_region IS 'Natural-key dimension: region. Independent source-domain meanings apply.';
```

Store documentation on table dataco.dim_region: “Natural-key dimension: region. Independent source-domain meanings apply.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 7

```text
  7  COMMENT ON TABLE dataco.dim_shipping_mode IS 'Natural-key dimension: shipping mode. Independent source-domain meanings apply.';
```

Store documentation on table dataco.dim_shipping_mode: “Natural-key dimension: shipping mode. Independent source-domain meanings apply.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 8

```text
  8  COMMENT ON TABLE dataco.fact_delivery_performance IS 'One DataCo order with consistent shipment attributes and eligible-outcome flag.';
```

Store documentation on table dataco.fact_delivery_performance: “One DataCo order with consistent shipment attributes and eligible-outcome flag.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 9

```text
  9  COMMENT ON TABLE dataco.fact_orders IS 'One DataCo order line, uniquely keyed by order_item_id. Repeated order IDs are expected.';
```

Store documentation on table dataco.fact_orders: “One DataCo order line, uniquely keyed by order_item_id. Repeated order IDs are expected.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 10

```text
 10  COMMENT ON TABLE dataco.fact_profitability IS 'One DataCo order-line sales/profit record, not a duplicated order-level total.';
```

Store documentation on table dataco.fact_profitability: “One DataCo order-line sales/profit record, not a duplicated order-level total.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 11

```text
 11  COMMENT ON TABLE m5.bridge_date_event IS 'One calendar date/event pair; both source events supported; avoid sales join fanout.';
```

Store documentation on table m5.bridge_date_event: “One calendar date/event pair; both source events supported; avoid sales join fanout.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 12

```text
 12  COMMENT ON TABLE m5.dim_category IS 'Natural-key dimension: category. Independent source-domain meanings apply.';
```

Store documentation on table m5.dim_category: “Natural-key dimension: category. Independent source-domain meanings apply.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 13

```text
 13  COMMENT ON TABLE m5.dim_department IS 'Natural-key dimension: department. Independent source-domain meanings apply.';
```

Store documentation on table m5.dim_department: “Natural-key dimension: department. Independent source-domain meanings apply.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 14

```text
 14  COMMENT ON TABLE m5.dim_event IS 'Natural-key dimension: event. Independent source-domain meanings apply.';
```

Store documentation on table m5.dim_event: “Natural-key dimension: event. Independent source-domain meanings apply.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 15

```text
 15  COMMENT ON TABLE m5.dim_product IS 'Natural-key dimension: product. Independent source-domain meanings apply.';
```

Store documentation on table m5.dim_product: “Natural-key dimension: product. Independent source-domain meanings apply.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 16

```text
 16  COMMENT ON TABLE m5.dim_state IS 'Natural-key dimension: state. Independent source-domain meanings apply.';
```

Store documentation on table m5.dim_state: “Natural-key dimension: state. Independent source-domain meanings apply.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 17

```text
 17  COMMENT ON TABLE m5.dim_store IS 'Natural-key dimension: store. Independent source-domain meanings apply.';
```

Store documentation on table m5.dim_store: “Natural-key dimension: store. Independent source-domain meanings apply.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 18

```text
 18  COMMENT ON TABLE m5.fact_forecast IS 'One row per M5 item-store-origin-target-date-selected-model.';
```

Store documentation on table m5.fact_forecast: “One row per M5 item-store-origin-target-date-selected-model.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 19

```text
 19  COMMENT ON TABLE m5.fact_forecast_accuracy IS 'One row per item-store-origin-date-candidate model; keep model/fold filters explicit.';
```

Store documentation on table m5.fact_forecast_accuracy: “One row per item-store-origin-date-candidate model; keep model/fold filters explicit.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 20

```text
 20  COMMENT ON TABLE m5.fact_inventory_policy IS 'One row per item-store-as-of-service scenario; simulated inventory only.';
```

Store documentation on table m5.fact_inventory_policy: “One row per item-store-as-of-service scenario; simulated inventory only.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 21

```text
 21  COMMENT ON TABLE m5.fact_inventory_simulation IS 'One row per item-store-date-policy-scenario-run-service; simulated daily lost-sales replay.';
```

Store documentation on table m5.fact_inventory_simulation: “One row per item-store-date-policy-scenario-run-service; simulated daily lost-sales replay.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 22

```text
 22  COMMENT ON TABLE m5.fact_sales_daily IS 'One row per M5 item-store-calendar day. Recorded units and listed-price revenue.';
```

Store documentation on table m5.fact_sales_daily: “One row per M5 item-store-calendar day. Recorded units and listed-price revenue.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 23

```text
 23  COMMENT ON TABLE m5.fact_sell_price IS 'One row per M5 item-store-retail-week price.';
```

Store documentation on table m5.fact_sell_price: “One row per M5 item-store-retail-week price.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 24

```text
 24  COMMENT ON COLUMN common.dim_date.date_key IS 'Integer YYYYMMDD key derived from calendar date.';
```

Store documentation on column common.dim_date.date_key: “Integer YYYYMMDD key derived from calendar date.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 25

```text
 25  COMMENT ON COLUMN common.dim_date.date IS 'Calendar date represented by the observation or prediction.';
```

Store documentation on column common.dim_date.date: “Calendar date represented by the observation or prediction.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 26

```text
 26  COMMENT ON COLUMN common.dim_date.year IS 'Calendar year.';
```

Store documentation on column common.dim_date.year: “Calendar year.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 27

```text
 27  COMMENT ON COLUMN common.dim_date.month IS 'Calendar month 1–12.';
```

Store documentation on column common.dim_date.month: “Calendar month 1–12.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 28

```text
 28  COMMENT ON COLUMN common.dim_date.quarter IS 'Calendar quarter 1–4.';
```

Store documentation on column common.dim_date.quarter: “Calendar quarter 1–4.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 29

```text
 29  COMMENT ON COLUMN dataco.dim_customer_segment.customer_segment IS 'Normalized business customer segment; no personal identity.';
```

Store documentation on column dataco.dim_customer_segment.customer_segment: “Normalized business customer segment; no personal identity.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 30

```text
 30  COMMENT ON COLUMN dataco.dim_market.market IS 'Normalized DataCo market; independent of M5 geography.';
```

Store documentation on column dataco.dim_market.market: “Normalized DataCo market; independent of M5 geography.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 31

```text
 31  COMMENT ON COLUMN dataco.dim_order_date.date_key IS 'Integer YYYYMMDD key derived from calendar date.';
```

Store documentation on column dataco.dim_order_date.date_key: “Integer YYYYMMDD key derived from calendar date.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 32

```text
 32  COMMENT ON COLUMN dataco.dim_order_date.date IS 'Calendar date represented by the observation or prediction.';
```

Store documentation on column dataco.dim_order_date.date: “Calendar date represented by the observation or prediction.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 33

```text
 33  COMMENT ON COLUMN dataco.dim_order_date.year IS 'Calendar year.';
```

Store documentation on column dataco.dim_order_date.year: “Calendar year.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 34

```text
 34  COMMENT ON COLUMN dataco.dim_order_date.month IS 'Calendar month 1–12.';
```

Store documentation on column dataco.dim_order_date.month: “Calendar month 1–12.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 35

```text
 35  COMMENT ON COLUMN dataco.dim_order_date.quarter IS 'Calendar quarter 1–4.';
```

Store documentation on column dataco.dim_order_date.quarter: “Calendar quarter 1–4.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 36

```text
 36  COMMENT ON COLUMN dataco.dim_product_category.category IS 'Normalized DataCo product category; independent of M5 categories.';
```

Store documentation on column dataco.dim_product_category.category: “Normalized DataCo product category; independent of M5 categories.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 37

```text
 37  COMMENT ON COLUMN dataco.dim_region.region IS 'Normalized DataCo order region.';
```

Store documentation on column dataco.dim_region.region: “Normalized DataCo order region.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 38

```text
 38  COMMENT ON COLUMN dataco.dim_shipping_mode.shipping_mode IS 'Normalized DataCo shipping service name.';
```

Store documentation on column dataco.dim_shipping_mode.shipping_mode: “Normalized DataCo shipping service name.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 39

```text
 39  COMMENT ON COLUMN dataco.fact_delivery_performance.order_id IS 'DataCo business order key; repeated across order lines, not a customer identity.';
```

Store documentation on column dataco.fact_delivery_performance.order_id: “DataCo business order key; repeated across order lines, not a customer identity.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 40

```text
 40  COMMENT ON COLUMN dataco.fact_delivery_performance.date_key IS 'Integer YYYYMMDD key derived from calendar date.';
```

Store documentation on column dataco.fact_delivery_performance.date_key: “Integer YYYYMMDD key derived from calendar date.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 41

```text
 41  COMMENT ON COLUMN dataco.fact_delivery_performance.order_date IS 'Parsed DataCo order calendar date; time of day discarded.';
```

Store documentation on column dataco.fact_delivery_performance.order_date: “Parsed DataCo order calendar date; time of day discarded.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 42

```text
 42  COMMENT ON COLUMN dataco.fact_delivery_performance.shipping_mode IS 'Normalized DataCo shipping service name.';
```

Store documentation on column dataco.fact_delivery_performance.shipping_mode: “Normalized DataCo shipping service name.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 43

```text
 43  COMMENT ON COLUMN dataco.fact_delivery_performance.market IS 'Normalized DataCo market; independent of M5 geography.';
```

Store documentation on column dataco.fact_delivery_performance.market: “Normalized DataCo market; independent of M5 geography.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 44

```text
 44  COMMENT ON COLUMN dataco.fact_delivery_performance.region IS 'Normalized DataCo order region.';
```

Store documentation on column dataco.fact_delivery_performance.region: “Normalized DataCo order region.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 45

```text
 45  COMMENT ON COLUMN dataco.fact_delivery_performance.customer_segment IS 'Normalized business customer segment; no personal identity.';
```

Store documentation on column dataco.fact_delivery_performance.customer_segment: “Normalized business customer segment; no personal identity.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 46

```text
 46  COMMENT ON COLUMN dataco.fact_delivery_performance.actual_shipping_days IS 'Source reported actual shipping duration in days; not last-mile scan evidence.';
```

Store documentation on column dataco.fact_delivery_performance.actual_shipping_days: “Source reported actual shipping duration in days; not last-mile scan evidence.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 47

```text
 47  COMMENT ON COLUMN dataco.fact_delivery_performance.scheduled_shipping_days IS 'Source promised shipping duration in days.';
```

Store documentation on column dataco.fact_delivery_performance.scheduled_shipping_days: “Source promised shipping duration in days.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 48

```text
 48  COMMENT ON COLUMN dataco.fact_delivery_performance.delivery_eligible IS 'True for valid 0–configured-max shipping durations excluding cancelled/suspected-fraud orders.';
```

Store documentation on column dataco.fact_delivery_performance.delivery_eligible: “True for valid 0–configured-max shipping durations excluding cancelled/suspected-fraud orders.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 49

```text
 49  COMMENT ON COLUMN dataco.fact_delivery_performance.late_order IS '1 when actual shipping exceeds scheduled, 0 when on time, null if ineligible.';
```

Store documentation on column dataco.fact_delivery_performance.late_order: “1 when actual shipping exceeds scheduled, 0 when on time, null if ineligible.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 50

```text
 50  COMMENT ON COLUMN dataco.fact_delivery_performance.delay_days IS 'Signed actual minus scheduled shipping days on eligible orders.';
```

Store documentation on column dataco.fact_delivery_performance.delay_days: “Signed actual minus scheduled shipping days on eligible orders.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 51

```text
 51  COMMENT ON COLUMN dataco.fact_delivery_performance.positive_delay_days IS 'Maximum of signed delay and zero; null if ineligible.';
```

Store documentation on column dataco.fact_delivery_performance.positive_delay_days: “Maximum of signed delay and zero; null if ineligible.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 52

```text
 52  COMMENT ON COLUMN dataco.fact_orders.order_item_id IS 'Unique DataCo business order-line key.';
```

Store documentation on column dataco.fact_orders.order_item_id: “Unique DataCo business order-line key.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 53

```text
 53  COMMENT ON COLUMN dataco.fact_orders.order_id IS 'DataCo business order key; repeated across order lines, not a customer identity.';
```

Store documentation on column dataco.fact_orders.order_id: “DataCo business order key; repeated across order lines, not a customer identity.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 54

```text
 54  COMMENT ON COLUMN dataco.fact_orders.date_key IS 'Integer YYYYMMDD key derived from calendar date.';
```

Store documentation on column dataco.fact_orders.date_key: “Integer YYYYMMDD key derived from calendar date.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 55

```text
 55  COMMENT ON COLUMN dataco.fact_orders.order_date IS 'Parsed DataCo order calendar date; time of day discarded.';
```

Store documentation on column dataco.fact_orders.order_date: “Parsed DataCo order calendar date; time of day discarded.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 56

```text
 56  COMMENT ON COLUMN dataco.fact_orders.category IS 'Normalized DataCo product category; independent of M5 categories.';
```

Store documentation on column dataco.fact_orders.category: “Normalized DataCo product category; independent of M5 categories.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 57

```text
 57  COMMENT ON COLUMN dataco.fact_orders.market IS 'Normalized DataCo market; independent of M5 geography.';
```

Store documentation on column dataco.fact_orders.market: “Normalized DataCo market; independent of M5 geography.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 58

```text
 58  COMMENT ON COLUMN dataco.fact_orders.region IS 'Normalized DataCo order region.';
```

Store documentation on column dataco.fact_orders.region: “Normalized DataCo order region.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 59

```text
 59  COMMENT ON COLUMN dataco.fact_orders.shipping_mode IS 'Normalized DataCo shipping service name.';
```

Store documentation on column dataco.fact_orders.shipping_mode: “Normalized DataCo shipping service name.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 60

```text
 60  COMMENT ON COLUMN dataco.fact_orders.customer_segment IS 'Normalized business customer segment; no personal identity.';
```

Store documentation on column dataco.fact_orders.customer_segment: “Normalized business customer segment; no personal identity.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 61

```text
 61  COMMENT ON COLUMN dataco.fact_orders.product_name IS 'Normalized DataCo product label.';
```

Store documentation on column dataco.fact_orders.product_name: “Normalized DataCo product label.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 62

```text
 62  COMMENT ON COLUMN dataco.fact_orders.quantity IS 'Source DataCo order-line quantity.';
```

Store documentation on column dataco.fact_orders.quantity: “Source DataCo order-line quantity.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 63

```text
 63  COMMENT ON COLUMN dataco.fact_orders.sales IS 'Configured DataCo line net-sales amount; defaults to order_item_total.';
```

Store documentation on column dataco.fact_orders.sales: “Configured DataCo line net-sales amount; defaults to order_item_total.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 64

```text
 64  COMMENT ON COLUMN dataco.fact_orders.profit IS 'Configured DataCo line benefit amount; defaults to benefit_per_order; not repeated alias sum.';
```

Store documentation on column dataco.fact_orders.profit: “Configured DataCo line benefit amount; defaults to benefit_per_order; not repeated alias sum.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 65

```text
 65  COMMENT ON COLUMN dataco.fact_orders.invalid_sales_flag IS 'Negative configured sales or negative quantity; excluded from headline profit measures.';
```

Store documentation on column dataco.fact_orders.invalid_sales_flag: “Negative configured sales or negative quantity; excluded from headline profit measures.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 66

```text
 66  COMMENT ON COLUMN dataco.fact_orders.abnormal_profit_flag IS 'Absolute line profit greater than twice absolute line sales; flag only, not automatic deletion.';
```

Store documentation on column dataco.fact_orders.abnormal_profit_flag: “Absolute line profit greater than twice absolute line sales; flag only, not automatic deletion.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 67

```text
 67  COMMENT ON COLUMN dataco.fact_profitability.order_item_id IS 'Unique DataCo business order-line key.';
```

Store documentation on column dataco.fact_profitability.order_item_id: “Unique DataCo business order-line key.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 68

```text
 68  COMMENT ON COLUMN dataco.fact_profitability.sales IS 'Configured DataCo line net-sales amount; defaults to order_item_total.';
```

Store documentation on column dataco.fact_profitability.sales: “Configured DataCo line net-sales amount; defaults to order_item_total.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 69

```text
 69  COMMENT ON COLUMN dataco.fact_profitability.profit IS 'Configured DataCo line benefit amount; defaults to benefit_per_order; not repeated alias sum.';
```

Store documentation on column dataco.fact_profitability.profit: “Configured DataCo line benefit amount; defaults to benefit_per_order; not repeated alias sum.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 70

```text
 70  COMMENT ON COLUMN dataco.fact_profitability.profit_margin IS 'Aggregate or line profit / matching sales, depending on table grain; undefined at zero sales.';
```

Store documentation on column dataco.fact_profitability.profit_margin: “Aggregate or line profit / matching sales, depending on table grain; undefined at zero sales.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 71

```text
 71  COMMENT ON COLUMN dataco.fact_profitability.loss_making_line IS 'True if a DataCo line has negative configured profit.';
```

Store documentation on column dataco.fact_profitability.loss_making_line: “True if a DataCo line has negative configured profit.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 72

```text
 72  COMMENT ON COLUMN m5.bridge_date_event.date_key IS 'Integer YYYYMMDD key derived from calendar date.';
```

Store documentation on column m5.bridge_date_event.date_key: “Integer YYYYMMDD key derived from calendar date.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 73

```text
 73  COMMENT ON COLUMN m5.bridge_date_event.event_name IS 'First source calendar event name; nullable.';
```

Store documentation on column m5.bridge_date_event.event_name: “First source calendar event name; nullable.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 74

```text
 74  COMMENT ON COLUMN m5.dim_category.category_id IS 'M5 category natural key.';
```

Store documentation on column m5.dim_category.category_id: “M5 category natural key.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 75

```text
 75  COMMENT ON COLUMN m5.dim_department.department_id IS 'M5 department natural key.';
```

Store documentation on column m5.dim_department.department_id: “M5 department natural key.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 76

```text
 76  COMMENT ON COLUMN m5.dim_department.category_id IS 'M5 category natural key.';
```

Store documentation on column m5.dim_department.category_id: “M5 category natural key.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 77

```text
 77  COMMENT ON COLUMN m5.dim_event.event_name IS 'First source calendar event name; nullable.';
```

Store documentation on column m5.dim_event.event_name: “First source calendar event name; nullable.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 78

```text
 78  COMMENT ON COLUMN m5.dim_event.event_type IS 'First source calendar event type; nullable.';
```

Store documentation on column m5.dim_event.event_type: “First source calendar event type; nullable.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 79

```text
 79  COMMENT ON COLUMN m5.dim_product.item_id IS 'M5 item natural key; not a DataCo product identifier.';
```

Store documentation on column m5.dim_product.item_id: “M5 item natural key; not a DataCo product identifier.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 80

```text
 80  COMMENT ON COLUMN m5.dim_product.department_id IS 'M5 department natural key.';
```

Store documentation on column m5.dim_product.department_id: “M5 department natural key.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 81

```text
 81  COMMENT ON COLUMN m5.dim_product.category_id IS 'M5 category natural key.';
```

Store documentation on column m5.dim_product.category_id: “M5 category natural key.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 82

```text
 82  COMMENT ON COLUMN m5.dim_state.state_id IS 'M5 state code CA, TX or WI.';
```

Store documentation on column m5.dim_state.state_id: “M5 state code CA, TX or WI.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 83

```text
 83  COMMENT ON COLUMN m5.dim_store.store_id IS 'M5 store natural key.';
```

Store documentation on column m5.dim_store.store_id: “M5 store natural key.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 84

```text
 84  COMMENT ON COLUMN m5.dim_store.state_id IS 'M5 state code CA, TX or WI.';
```

Store documentation on column m5.dim_store.state_id: “M5 state code CA, TX or WI.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 85

```text
 85  COMMENT ON COLUMN m5.fact_forecast.item_id IS 'M5 item natural key; not a DataCo product identifier.';
```

Store documentation on column m5.fact_forecast.item_id: “M5 item natural key; not a DataCo product identifier.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 86

```text
 86  COMMENT ON COLUMN m5.fact_forecast.store_id IS 'M5 store natural key.';
```

Store documentation on column m5.fact_forecast.store_id: “M5 store natural key.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 87

```text
 87  COMMENT ON COLUMN m5.fact_forecast.date_key IS 'Integer YYYYMMDD key derived from calendar date.';
```

Store documentation on column m5.fact_forecast.date_key: “Integer YYYYMMDD key derived from calendar date.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 88

```text
 88  COMMENT ON COLUMN m5.fact_forecast.origin IS 'Last historical date available to the forecast.';
```

Store documentation on column m5.fact_forecast.origin: “Last historical date available to the forecast.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 89

```text
 89  COMMENT ON COLUMN m5.fact_forecast.date IS 'Calendar date represented by the observation or prediction.';
```

Store documentation on column m5.fact_forecast.date: “Calendar date represented by the observation or prediction.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 90

```text
 90  COMMENT ON COLUMN m5.fact_forecast.horizon IS 'Integer number of days after origin.';
```

Store documentation on column m5.fact_forecast.horizon: “Integer number of days after origin.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 91

```text
 91  COMMENT ON COLUMN m5.fact_forecast.model IS 'Forecast or classifier name; different forecast levels must not be pooled.';
```

Store documentation on column m5.fact_forecast.model: “Forecast or classifier name; different forecast levels must not be pooled.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 92

```text
 92  COMMENT ON COLUMN m5.fact_forecast.forecast_units IS 'Nonnegative model prediction in units for one item-store-date-origin-model.';
```

Store documentation on column m5.fact_forecast.forecast_units: “Nonnegative model prediction in units for one item-store-date-origin-model.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 93

```text
 93  COMMENT ON COLUMN m5.fact_forecast.lower_80 IS 'Lower empirical residual bound for nominal 80% interval, clipped at zero and below point.';
```

Store documentation on column m5.fact_forecast.lower_80: “Lower empirical residual bound for nominal 80% interval, clipped at zero and below point.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 94

```text
 94  COMMENT ON COLUMN m5.fact_forecast.upper_80 IS 'Upper empirical residual bound for nominal 80% interval, at least point forecast.';
```

Store documentation on column m5.fact_forecast.upper_80: “Upper empirical residual bound for nominal 80% interval, at least point forecast.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 95

```text
 95  COMMENT ON COLUMN m5.fact_forecast.lower_95 IS 'Lower empirical residual bound for nominal 95% interval; not additive into portfolio coverage.';
```

Store documentation on column m5.fact_forecast.lower_95: “Lower empirical residual bound for nominal 95% interval; not additive into portfolio coverage.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 96

```text
 96  COMMENT ON COLUMN m5.fact_forecast.upper_95 IS 'Upper empirical residual bound for nominal 95% interval; not additive into portfolio coverage.';
```

Store documentation on column m5.fact_forecast.upper_95: “Upper empirical residual bound for nominal 95% interval; not additive into portfolio coverage.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 97

```text
 97  COMMENT ON COLUMN m5.fact_forecast_accuracy.item_id IS 'M5 item natural key; not a DataCo product identifier.';
```

Store documentation on column m5.fact_forecast_accuracy.item_id: “M5 item natural key; not a DataCo product identifier.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 98

```text
 98  COMMENT ON COLUMN m5.fact_forecast_accuracy.store_id IS 'M5 store natural key.';
```

Store documentation on column m5.fact_forecast_accuracy.store_id: “M5 store natural key.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 99

```text
 99  COMMENT ON COLUMN m5.fact_forecast_accuracy.date_key IS 'Integer YYYYMMDD key derived from calendar date.';
```

Store documentation on column m5.fact_forecast_accuracy.date_key: “Integer YYYYMMDD key derived from calendar date.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 100

```text
100  COMMENT ON COLUMN m5.fact_forecast_accuracy.origin IS 'Last historical date available to the forecast.';
```

Store documentation on column m5.fact_forecast_accuracy.origin: “Last historical date available to the forecast.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 101

```text
101  COMMENT ON COLUMN m5.fact_forecast_accuracy.date IS 'Calendar date represented by the observation or prediction.';
```

Store documentation on column m5.fact_forecast_accuracy.date: “Calendar date represented by the observation or prediction.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 102

```text
102  COMMENT ON COLUMN m5.fact_forecast_accuracy.model IS 'Forecast or classifier name; different forecast levels must not be pooled.';
```

Store documentation on column m5.fact_forecast_accuracy.model: “Forecast or classifier name; different forecast levels must not be pooled.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 103

```text
103  COMMENT ON COLUMN m5.fact_forecast_accuracy.fold IS 'Chronological rolling-origin fold index.';
```

Store documentation on column m5.fact_forecast_accuracy.fold: “Chronological rolling-origin fold index.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 104

```text
104  COMMENT ON COLUMN m5.fact_forecast_accuracy.split_role IS 'Calibration, selection or locked test role.';
```

Store documentation on column m5.fact_forecast_accuracy.split_role: “Calibration, selection or locked test role.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 105

```text
105  COMMENT ON COLUMN m5.fact_forecast_accuracy.actual_units IS 'Observed held-out M5 sales units matched to a forecast.';
```

Store documentation on column m5.fact_forecast_accuracy.actual_units: “Observed held-out M5 sales units matched to a forecast.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 106

```text
106  COMMENT ON COLUMN m5.fact_forecast_accuracy.forecast_units IS 'Nonnegative model prediction in units for one item-store-date-origin-model.';
```

Store documentation on column m5.fact_forecast_accuracy.forecast_units: “Nonnegative model prediction in units for one item-store-date-origin-model.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 107

```text
107  COMMENT ON COLUMN m5.fact_forecast_accuracy.error IS 'Forecast units minus actual units; positive means overprediction.';
```

Store documentation on column m5.fact_forecast_accuracy.error: “Forecast units minus actual units; positive means overprediction.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 108

```text
108  COMMENT ON COLUMN m5.fact_forecast_accuracy.absolute_error IS 'Absolute value of row prediction error.';
```

Store documentation on column m5.fact_forecast_accuracy.absolute_error: “Absolute value of row prediction error.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 109

```text
109  COMMENT ON COLUMN m5.fact_forecast_accuracy.scale IS 'Mean squared training first difference after first nonzero sale; undefined for constants.';
```

Store documentation on column m5.fact_forecast_accuracy.scale: “Mean squared training first difference after first nonzero sale; undefined for constants.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 110

```text
110  COMMENT ON COLUMN m5.fact_inventory_policy.item_id IS 'M5 item natural key; not a DataCo product identifier.';
```

Store documentation on column m5.fact_inventory_policy.item_id: “M5 item natural key; not a DataCo product identifier.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 111

```text
111  COMMENT ON COLUMN m5.fact_inventory_policy.store_id IS 'M5 store natural key.';
```

Store documentation on column m5.fact_inventory_policy.store_id: “M5 store natural key.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 112

```text
112  COMMENT ON COLUMN m5.fact_inventory_policy.as_of_date IS 'Snapshot date at which an inventory recommendation was generated.';
```

Store documentation on column m5.fact_inventory_policy.as_of_date: “Snapshot date at which an inventory recommendation was generated.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 113

```text
113  COMMENT ON COLUMN m5.fact_inventory_policy.target_service_level IS 'Scenario cycle-service target in (0,1); does not equal fill rate.';
```

Store documentation on column m5.fact_inventory_policy.target_service_level: “Scenario cycle-service target in (0,1); does not equal fill rate.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 114

```text
114  COMMENT ON COLUMN m5.fact_inventory_policy.average_daily_demand IS 'Trailing 90-day pre-origin recorded-sales mean for an item-store.';
```

Store documentation on column m5.fact_inventory_policy.average_daily_demand: “Trailing 90-day pre-origin recorded-sales mean for an item-store.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 115

```text
115  COMMENT ON COLUMN m5.fact_inventory_policy.forecast_daily_demand IS 'Mean predicted daily units over the planning horizon.';
```

Store documentation on column m5.fact_inventory_policy.forecast_daily_demand: “Mean predicted daily units over the planning horizon.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 116

```text
116  COMMENT ON COLUMN m5.fact_inventory_policy.initial_inventory IS 'Assumed opening on-hand units before first simulation demand.';
```

Store documentation on column m5.fact_inventory_policy.initial_inventory: “Assumed opening on-hand units before first simulation demand.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 117

```text
117  COMMENT ON COLUMN m5.fact_inventory_policy.estimated_unit_cost IS 'Assumed cost-to-price ratio times last known price, with positive floor.';
```

Store documentation on column m5.fact_inventory_policy.estimated_unit_cost: “Assumed cost-to-price ratio times last known price, with positive floor.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 118

```text
118  COMMENT ON COLUMN m5.fact_inventory_policy.safety_stock IS 'Normal-approximation lead-time buffer units based on assumed service level.';
```

Store documentation on column m5.fact_inventory_policy.safety_stock: “Normal-approximation lead-time buffer units based on assumed service level.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 119

```text
119  COMMENT ON COLUMN m5.fact_inventory_policy.reorder_point IS 'Expected lead-time demand plus lead-time safety stock; continuous-review reference.';
```

Store documentation on column m5.fact_inventory_policy.reorder_point: “Expected lead-time demand plus lead-time safety stock; continuous-review reference.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 120

```text
120  COMMENT ON COLUMN m5.fact_inventory_policy.eoq IS 'Square root of 2 × annualized units × fixed ordering cost / annual per-unit holding cost.';
```

Store documentation on column m5.fact_inventory_policy.eoq: “Square root of 2 × annualized units × fixed ordering cost / annual per-unit holding cost.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 121

```text
121  COMMENT ON COLUMN m5.fact_inventory_policy.days_of_supply IS 'Assumed initial inventory / forecast daily mean; undefined for zero mean.';
```

Store documentation on column m5.fact_inventory_policy.days_of_supply: “Assumed initial inventory / forecast daily mean; undefined for zero mean.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 122

```text
122  COMMENT ON COLUMN m5.fact_inventory_policy.inventory_value IS 'Assumed initial stock multiplied by estimated unit cost.';
```

Store documentation on column m5.fact_inventory_policy.inventory_value: “Assumed initial stock multiplied by estimated unit cost.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 123

```text
123  COMMENT ON COLUMN m5.fact_inventory_policy.stockout_probability IS 'Normal lead-time demand tail above initial stock assuming no initial incoming POs.';
```

Store documentation on column m5.fact_inventory_policy.stockout_probability: “Normal lead-time demand tail above initial stock assuming no initial incoming POs.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 124

```text
124  COMMENT ON COLUMN m5.fact_inventory_policy.recommended_order_quantity IS 'Larger of EOQ or target shortage, rounded to MOQ/case pack, zero if no shortage.';
```

Store documentation on column m5.fact_inventory_policy.recommended_order_quantity: “Larger of EOQ or target shortage, rounded to MOQ/case pack, zero if no shortage.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 125

```text
125  COMMENT ON COLUMN m5.fact_inventory_policy.excess_units IS 'Positive initial inventory above protection order-up-to target.';
```

Store documentation on column m5.fact_inventory_policy.excess_units: “Positive initial inventory above protection order-up-to target.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 126

```text
126  COMMENT ON COLUMN m5.fact_inventory_policy.excess_value IS 'Excess units multiplied by estimated unit cost.';
```

Store documentation on column m5.fact_inventory_policy.excess_value: “Excess units multiplied by estimated unit cost.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 127

```text
127  COMMENT ON COLUMN m5.fact_inventory_simulation.item_id IS 'M5 item natural key; not a DataCo product identifier.';
```

Store documentation on column m5.fact_inventory_simulation.item_id: “M5 item natural key; not a DataCo product identifier.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 128

```text
128  COMMENT ON COLUMN m5.fact_inventory_simulation.store_id IS 'M5 store natural key.';
```

Store documentation on column m5.fact_inventory_simulation.store_id: “M5 store natural key.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 129

```text
129  COMMENT ON COLUMN m5.fact_inventory_simulation.date IS 'Calendar date represented by the observation or prediction.';
```

Store documentation on column m5.fact_inventory_simulation.date: “Calendar date represented by the observation or prediction.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 130

```text
130  COMMENT ON COLUMN m5.fact_inventory_simulation.policy IS 'baseline or optimized replenishment policy.';
```

Store documentation on column m5.fact_inventory_simulation.policy: “baseline or optimized replenishment policy.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 131

```text
131  COMMENT ON COLUMN m5.fact_inventory_simulation.scenario IS 'Base or named one-factor-at-a-time sensitivity case.';
```

Store documentation on column m5.fact_inventory_simulation.scenario: “Base or named one-factor-at-a-time sensitivity case.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 132

```text
132  COMMENT ON COLUMN m5.fact_inventory_simulation.run_id IS 'Monte Carlo repeat index; average repeated worlds rather than summing.';
```

Store documentation on column m5.fact_inventory_simulation.run_id: “Monte Carlo repeat index; average repeated worlds rather than summing.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 133

```text
133  COMMENT ON COLUMN m5.fact_inventory_simulation.target_service_level IS 'Scenario cycle-service target in (0,1); does not equal fill rate.';
```

Store documentation on column m5.fact_inventory_simulation.target_service_level: “Scenario cycle-service target in (0,1); does not equal fill rate.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 134

```text
134  COMMENT ON COLUMN m5.fact_inventory_simulation.opening_inventory IS 'On-hand units before today''s receipts and demand.';
```

Store documentation on column m5.fact_inventory_simulation.opening_inventory: “On-hand units before today's receipts and demand.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 135

```text
135  COMMENT ON COLUMN m5.fact_inventory_simulation.arrivals IS 'Units received today from previously placed purchase orders.';
```

Store documentation on column m5.fact_inventory_simulation.arrivals: “Units received today from previously placed purchase orders.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 136

```text
136  COMMENT ON COLUMN m5.fact_inventory_simulation.actual_demand IS 'Recorded held-out sales used as simulation demand proxy, not uncensored demand.';
```

Store documentation on column m5.fact_inventory_simulation.actual_demand: “Recorded held-out sales used as simulation demand proxy, not uncensored demand.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 137

```text
137  COMMENT ON COLUMN m5.fact_inventory_simulation.forecast_demand IS 'Daily origin-time forecast passed into inventory replay.';
```

Store documentation on column m5.fact_inventory_simulation.forecast_demand: “Daily origin-time forecast passed into inventory replay.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 138

```text
138  COMMENT ON COLUMN m5.fact_inventory_simulation.fulfilled_units IS 'Minimum of available inventory and observed demand proxy.';
```

Store documentation on column m5.fact_inventory_simulation.fulfilled_units: “Minimum of available inventory and observed demand proxy.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 139

```text
139  COMMENT ON COLUMN m5.fact_inventory_simulation.lost_sales_units IS 'Demand proxy minus fulfilled units; no backorders carried.';
```

Store documentation on column m5.fact_inventory_simulation.lost_sales_units: “Demand proxy minus fulfilled units; no backorders carried.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 140

```text
140  COMMENT ON COLUMN m5.fact_inventory_simulation.order_quantity IS 'Units ordered after today''s demand at a review opportunity.';
```

Store documentation on column m5.fact_inventory_simulation.order_quantity: “Units ordered after today's demand at a review opportunity.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 141

```text
141  COMMENT ON COLUMN m5.fact_inventory_simulation.in_transit_units IS 'All placed units still awaiting arrival at end of day, including new orders.';
```

Store documentation on column m5.fact_inventory_simulation.in_transit_units: “All placed units still awaiting arrival at end of day, including new orders.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 142

```text
142  COMMENT ON COLUMN m5.fact_inventory_simulation.closing_inventory IS 'Opening units plus receipts minus fulfillment; nonnegative.';
```

Store documentation on column m5.fact_inventory_simulation.closing_inventory: “Opening units plus receipts minus fulfillment; nonnegative.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 143

```text
143  COMMENT ON COLUMN m5.fact_inventory_simulation.stockout_event IS '1 when any demand is lost on the item-store-day.';
```

Store documentation on column m5.fact_inventory_simulation.stockout_event: “1 when any demand is lost on the item-store-day.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 144

```text
144  COMMENT ON COLUMN m5.fact_inventory_simulation.holding_cost IS 'Closing units × unit cost × annual holding rate / 365.';
```

Store documentation on column m5.fact_inventory_simulation.holding_cost: “Closing units × unit cost × annual holding rate / 365.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 145

```text
145  COMMENT ON COLUMN m5.fact_inventory_simulation.ordering_cost IS 'Fixed assumed order cost if a positive order was placed, otherwise zero.';
```

Store documentation on column m5.fact_inventory_simulation.ordering_cost: “Fixed assumed order cost if a positive order was placed, otherwise zero.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 146

```text
146  COMMENT ON COLUMN m5.fact_inventory_simulation.lost_sale_cost IS 'Lost units multiplied by assumed lost-sale penalty.';
```

Store documentation on column m5.fact_inventory_simulation.lost_sale_cost: “Lost units multiplied by assumed lost-sale penalty.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 147

```text
147  COMMENT ON COLUMN m5.fact_inventory_simulation.total_inventory_cost IS 'Holding + ordering + lost-sale cost; excludes purchase spend and terminal valuation.';
```

Store documentation on column m5.fact_inventory_simulation.total_inventory_cost: “Holding + ordering + lost-sale cost; excludes purchase spend and terminal valuation.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 148

```text
148  COMMENT ON COLUMN m5.fact_inventory_simulation.lost_sales_value IS 'Lost units valued at origin-time selling price; hypothetical revenue loss.';
```

Store documentation on column m5.fact_inventory_simulation.lost_sales_value: “Lost units valued at origin-time selling price; hypothetical revenue loss.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 149

```text
149  COMMENT ON COLUMN m5.fact_inventory_simulation.estimated_unit_cost IS 'Assumed cost-to-price ratio times last known price, with positive floor.';
```

Store documentation on column m5.fact_inventory_simulation.estimated_unit_cost: “Assumed cost-to-price ratio times last known price, with positive floor.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 150

```text
150  COMMENT ON COLUMN m5.fact_inventory_simulation.completed_cycles IS 'Completed receipt-to-receipt replenishment cycles; first and unfinished cycles excluded.';
```

Store documentation on column m5.fact_inventory_simulation.completed_cycles: “Completed receipt-to-receipt replenishment cycles; first and unfinished cycles excluded.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 151

```text
151  COMMENT ON COLUMN m5.fact_inventory_simulation.successful_cycles IS 'Completed cycles with no lost demand between consecutive receipts.';
```

Store documentation on column m5.fact_inventory_simulation.successful_cycles: “Completed cycles with no lost demand between consecutive receipts.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 152

```text
152  COMMENT ON COLUMN m5.fact_sales_daily.item_id IS 'M5 item natural key; not a DataCo product identifier.';
```

Store documentation on column m5.fact_sales_daily.item_id: “M5 item natural key; not a DataCo product identifier.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 153

```text
153  COMMENT ON COLUMN m5.fact_sales_daily.store_id IS 'M5 store natural key.';
```

Store documentation on column m5.fact_sales_daily.store_id: “M5 store natural key.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 154

```text
154  COMMENT ON COLUMN m5.fact_sales_daily.date_key IS 'Integer YYYYMMDD key derived from calendar date.';
```

Store documentation on column m5.fact_sales_daily.date_key: “Integer YYYYMMDD key derived from calendar date.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 155

```text
155  COMMENT ON COLUMN m5.fact_sales_daily.date IS 'Calendar date represented by the observation or prediction.';
```

Store documentation on column m5.fact_sales_daily.date: “Calendar date represented by the observation or prediction.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 156

```text
156  COMMENT ON COLUMN m5.fact_sales_daily.units_sold IS 'M5 recorded sales units; availability-censored demand is possible.';
```

Store documentation on column m5.fact_sales_daily.units_sold: “M5 recorded sales units; availability-censored demand is possible.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 157

```text
157  COMMENT ON COLUMN m5.fact_sales_daily.sell_price IS 'M5 listed weekly item-store selling price, source currency per unit.';
```

Store documentation on column m5.fact_sales_daily.sell_price: “M5 listed weekly item-store selling price, source currency per unit.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 158

```text
158  COMMENT ON COLUMN m5.fact_sales_daily.revenue IS 'M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price.';
```

Store documentation on column m5.fact_sales_daily.revenue: “M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 159

```text
159  COMMENT ON COLUMN m5.fact_sales_daily.wm_yr_wk IS 'M5 retail calendar week identifier.';
```

Store documentation on column m5.fact_sales_daily.wm_yr_wk: “M5 retail calendar week identifier.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 160

```text
160  COMMENT ON COLUMN m5.fact_sales_daily.snap_flag IS 'Source state-specific SNAP eligibility indicator, 0 or 1; not a promotion flag.';
```

Store documentation on column m5.fact_sales_daily.snap_flag: “Source state-specific SNAP eligibility indicator, 0 or 1; not a promotion flag.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 161

```text
161  COMMENT ON COLUMN m5.fact_sales_daily.event_flag IS '1 if either source event is present on the date.';
```

Store documentation on column m5.fact_sales_daily.event_flag: “1 if either source event is present on the date.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 162

```text
162  COMMENT ON COLUMN m5.fact_sell_price.item_id IS 'M5 item natural key; not a DataCo product identifier.';
```

Store documentation on column m5.fact_sell_price.item_id: “M5 item natural key; not a DataCo product identifier.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 163

```text
163  COMMENT ON COLUMN m5.fact_sell_price.store_id IS 'M5 store natural key.';
```

Store documentation on column m5.fact_sell_price.store_id: “M5 store natural key.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 164

```text
164  COMMENT ON COLUMN m5.fact_sell_price.wm_yr_wk IS 'M5 retail calendar week identifier.';
```

Store documentation on column m5.fact_sell_price.wm_yr_wk: “M5 retail calendar week identifier.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


### Line 165

```text
165  COMMENT ON COLUMN m5.fact_sell_price.sell_price IS 'M5 listed weekly item-store selling price, source currency per unit.';
```

Store documentation on column m5.fact_sell_price.sell_price: “M5 listed weekly item-store selling price, source currency per unit.” This changes database metadata, not row values or arithmetic. Comments help SQL/BI users interpret grain and provenance; this later file can replace an earlier comment on the same object.


## sql/interview_queries.sql

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1–2

```text
  1  -- 1. Monthly units and revenue
  2  SELECT date_trunc('month',date) AS month,sum(units_sold) units,sum(revenue) revenue FROM m5.fact_sales_daily GROUP BY 1 ORDER BY 1;
```

Question 1: aggregate daily facts into calendar-month units/revenue and order chronologically. Aggregation is performed before presenting trends.


### Line 3

```text
  3
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 4–5

```text
  4  -- 2. Month-over-month growth
  5  WITH m AS (SELECT date_trunc('month',date) AS month,sum(revenue) revenue FROM m5.fact_sales_daily GROUP BY 1) SELECT *,revenue/nullif(lag(revenue) OVER(ORDER BY month),0)-1 mom_growth FROM m;
```

Question 2: use a monthly CTE then LAG to compare the previous available month's revenue. NULLIF protects a zero base. Missing months are not filled, so previous row may differ from previous calendar month on incomplete data.


### Line 6

```text
  6
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 7–8

```text
  7  -- 3. Store revenue ranking
  8  SELECT store_id,sum(revenue) revenue,dense_rank() OVER(ORDER BY sum(revenue) DESC) rank FROM m5.fact_sales_daily GROUP BY 1;
```

Question 3: sum each store's revenue then dense-rank; tied stores share rank without gaps.


### Line 9

```text
  9
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 10–11

```text
 10  -- 4. Category contribution
 11  SELECT p.category_id,sum(f.revenue) revenue,sum(f.revenue)/nullif(sum(sum(f.revenue)) OVER(),0) contribution FROM m5.fact_sales_daily f JOIN m5.dim_product p USING(item_id) GROUP BY 1;
```

Question 4: join unique product descriptions, aggregate categories and divide by a windowed total of category totals to obtain revenue share.


### Line 12

```text
 12
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 13–14

```text
 13  -- 5. Top products: trailing 90 days
 14  SELECT item_id,sum(revenue) revenue FROM m5.fact_sales_daily WHERE date>(SELECT max(date)-89 FROM m5.fact_sales_daily)-1 GROUP BY 1 ORDER BY 2 DESC LIMIT 20;
```

Question 5: take the final inclusive 90-day window relative to the dataset end, not today's wall clock, then rank item revenue. The max(date)-89-1 arithmetic is compact but less readable than an explicit interval.


### Line 15

```text
 15
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 16–17

```text
 16  -- 6. Bottom products; retain zero-demand items
 17  SELECT item_id,sum(revenue) revenue FROM m5.fact_sales_daily GROUP BY 1 ORDER BY 2 ASC NULLS LAST LIMIT 20;
```

Question 6: retain zero-selling products represented in the facts and find smallest revenues. Entirely absent products cannot be discovered without a complete external catalog.


### Line 18

```text
 18
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 19–20

```text
 19  -- 7. Past-only rolling demand
 20  SELECT item_id,store_id,date,avg(units_sold) OVER(PARTITION BY item_id,store_id ORDER BY date ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) mean7,avg(units_sold) OVER(PARTITION BY item_id,store_id ORDER BY date ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING) mean28 FROM m5.fact_sales_daily;
```

Question 7: calculate pair-specific rolling means with windows ending before the current day to demonstrate past-only SQL features.


### Line 21

```text
 21
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 22–23

```text
 22  -- 8. Variability and zero frequency
 23  SELECT item_id,store_id,stddev_samp(units_sold)/nullif(avg(units_sold),0) cv,avg(CASE WHEN units_sold=0 THEN 1.0 ELSE 0 END) zero_share FROM m5.fact_sales_daily GROUP BY 1,2;
```

Question 8: summarize relative variability and zero-sales share together; mean/std alone can hide intermittent behavior.


### Line 24

```text
 24
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 25–26

```text
 25  -- 9. ABC, including the item that crosses a boundary
 26  WITH r AS (SELECT item_id,sum(revenue) revenue FROM m5.fact_sales_daily GROUP BY 1),c AS(SELECT *,coalesce(sum(revenue) OVER(ORDER BY revenue DESC,item_id ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0)/nullif(sum(revenue) OVER(),0) prior_share FROM r) SELECT *,CASE WHEN prior_share<.8 THEN 'A' WHEN prior_share<.95 THEN 'B' ELSE 'C' END abc FROM c;
```

Question 9: calculate item revenue and the share before the current item, then apply ABC thresholds. This example is item-level across stores, unlike the item-store Python segmentation.


### Line 27

```text
 27
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 28–29

```text
 28  -- 10. XYZ, CV thresholds are configurable planning heuristics
 29  SELECT item_id,store_id,CASE WHEN avg(CASE WHEN units_sold=0 THEN 1.0 ELSE 0 END)>=.5 THEN 'Z' WHEN stddev_samp(units_sold)/nullif(avg(units_sold),0)<=.5 THEN 'X' WHEN stddev_samp(units_sold)/nullif(avg(units_sold),0)<=1 THEN 'Y' ELSE 'Z' END xyz FROM m5.fact_sales_daily GROUP BY 1,2;
```

Question 10: classify pair stability with fixed illustrative CV/zero-share thresholds. The query's constants are not dynamically linked to YAML configuration.


### Line 30

```text
 30
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 31–32

```text
 31  -- 11. Combined ABC-XYZ at item-store grain
 32  WITH r AS(SELECT item_id,store_id,sum(revenue) revenue,stddev_samp(units_sold)/nullif(avg(units_sold),0) cv,avg(CASE WHEN units_sold=0 THEN 1.0 ELSE 0 END) zero_share FROM m5.fact_sales_daily GROUP BY 1,2), c AS(SELECT *,coalesce(sum(revenue) OVER(ORDER BY revenue DESC,item_id,store_id ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0)/nullif(sum(revenue) OVER(),0) prior_share FROM r) SELECT *,concat(CASE WHEN prior_share<.8 THEN 'A' WHEN prior_share<.95 THEN 'B' ELSE 'C' END,'-',CASE WHEN zero_share>=.5 THEN 'Z' WHEN cv<=.5 THEN 'X' WHEN cv<=1 THEN 'Y' ELSE 'Z' END) abc_xyz FROM c;
```

Question 11: combine revenue priority and demand variability at item-store grain over all loaded history. It will not necessarily match Python's trailing-90-day classifications.


### Line 33

```text
 33
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 34–35

```text
 34  -- 12. Price versus demand changes: descriptive, not causal
 35  SELECT item_id,store_id,date,sell_price/nullif(lag(sell_price) OVER w,0)-1 price_change,units_sold-lag(units_sold) OVER w demand_change,lead(units_sold) OVER w next_day_units FROM m5.fact_sales_daily WINDOW w AS(PARTITION BY item_id,store_id ORDER BY date);
```

Question 12: use LAG/LEAD to inspect price/demand relationships. next_day_units is legitimate for retrospective analysis but would leak if copied into a predictive feature matrix.


### Line 36

```text
 36
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 37–38

```text
 37  -- 13. Event association, unadjusted for seasonal confounding
 38  SELECT item_id,avg(units_sold) FILTER(WHERE event_flag=1)/nullif(avg(units_sold) FILTER(WHERE event_flag=0),0)-1 unadjusted_event_uplift FROM m5.fact_sales_daily GROUP BY 1;
```

Question 13: compare average event/non-event sales. Different seasons, weekday mix and product mix can confound this unadjusted association.


### Line 39

```text
 39
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 40–41

```text
 40  -- 14. Forecast WAPE by store; locked test only
 41  SELECT store_id,model,sum(absolute_error)/nullif(sum(actual_units),0) wape FROM m5.fact_forecast_accuracy WHERE split_role='test' GROUP BY 1,2;
```

Question 14: compare model WAPE by store on the locked-test role only. Candidate comparison here is reporting, not permission to reselect the deployed model using test outcomes.


### Line 42

```text
 42
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 43–44

```text
 43  -- 15. Forecast WAPE by category
 44  SELECT p.category_id,f.model,sum(f.absolute_error)/nullif(sum(f.actual_units),0) wape FROM m5.fact_forecast_accuracy f JOIN m5.dim_product p USING(item_id) WHERE split_role='test' GROUP BY 1,2;
```

Question 15: attach categories and compute test WAPE as a ratio of sums; do not average store or item WAPEs without considering weights.


### Line 45

```text
 45
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 46–47

```text
 46  -- 16. Highest modeled stockout risk; select one scenario
 47  SELECT * FROM m5.fact_inventory_policy WHERE target_service_level=.95 ORDER BY stockout_probability DESC LIMIT 20;
```

Question 16: rank modeled stockout risk at one service target. Multiple retained as-of snapshots would also need an as-of filter; current loader retains one snapshot.


### Line 48

```text
 48
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 49–50

```text
 49  -- 17. Excess simulated inventory
 50  SELECT item_id,store_id,excess_units,excess_value FROM m5.fact_inventory_policy WHERE target_service_level=.95 AND excess_units>0 ORDER BY excess_value DESC;
```

Question 17: select positive modeled excess at 95% service and rank capital value to prioritize review.


### Line 51

```text
 51
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 52–53

```text
 52  -- 18. Simulated inventory investment by category
 53  SELECT p.category_id,sum(i.inventory_value) value FROM m5.fact_inventory_policy i JOIN m5.dim_product p USING(item_id) WHERE target_service_level=.95 GROUP BY 1;
```

Question 18: aggregate simulated opening inventory investment by category after selecting one service target, avoiding tripling the same initial stock.


### Line 54

```text
 54
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 55–56

```text
 55  -- 19. Late rate by shipping mode, one row per order
 56  SELECT shipping_mode,count(*) eligible_orders,avg(late_order::numeric) late_rate FROM dataco.fact_delivery_performance WHERE delivery_eligible GROUP BY 1;
```

Question 19: calculate late share from eligible one-row-per-order records, which avoids giving multi-line orders extra weight.


### Line 57

```text
 57
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 58–59

```text
 58  -- 20. Delay by region, including on-time zero delay
 59  SELECT region,avg(positive_delay_days) average_delay,percentile_cont(.9) WITHIN GROUP(ORDER BY positive_delay_days) p90_delay FROM dataco.fact_delivery_performance WHERE delivery_eligible GROUP BY 1;
```

Question 20: show mean and 90th percentile positive delay by region, including zero for punctual orders. This differs from lateness severity among late orders alone.


### Line 60

```text
 60
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 61–62

```text
 61  -- 21. Profit margin by category, ratio of sums
 62  SELECT category,sum(profit)/nullif(sum(sales),0) margin FROM dataco.fact_orders WHERE NOT invalid_sales_flag GROUP BY 1;
```

Question 21: calculate category margin as total profit/total sales on valid lines, with a protected denominator.


### Line 63

```text
 63
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 64–65

```text
 64  -- 22. Loss-making orders after summing lines
 65  SELECT order_id,sum(sales) sales,sum(profit) profit FROM dataco.fact_orders WHERE NOT invalid_sales_flag GROUP BY 1 HAVING sum(profit)<0 ORDER BY 3;
```

Question 22: group lines into orders before HAVING total profit<0. WHERE filters input rows; HAVING filters aggregate groups.


### Line 66

```text
 66
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 67–68

```text
 67  -- 23. High-sales low-profit products: data-driven sales threshold
 68  WITH p AS(SELECT product_name,sum(sales) sales,sum(profit) profit FROM dataco.fact_orders WHERE NOT invalid_sales_flag GROUP BY 1) SELECT *,profit/nullif(sales,0) margin FROM p WHERE sales>=(SELECT percentile_cont(.75) WITHIN GROUP(ORDER BY sales) FROM p) AND profit/nullif(sales,0)<.05;
```

Question 23: create product totals, use a data-dependent 75th-percentile sales cutoff and a fixed <5% margin rule. It identifies candidates for investigation, not proven pricing problems.


### Line 69

```text
 69
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 70–71

```text
 70  -- 24. Pareto of late orders by region
 71  WITH r AS(SELECT region,sum(late_order) late_orders FROM dataco.fact_delivery_performance WHERE delivery_eligible GROUP BY 1) SELECT *,sum(late_orders) OVER(ORDER BY late_orders DESC,region)/nullif(sum(late_orders) OVER(),0)::numeric cumulative_share FROM r;
```

Question 24: rank regions by late-order count and compute cumulative share for prioritization. Numeric casting prevents integer division.


### Line 72

```text
 72
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 73–74

```text
 73  -- 25. Executive domains remain separate
 74  SELECT * FROM mart.mart_executive_kpis;
```

Question 25: inspect the executive view that preserves independent domain labels rather than inventing combined totals.


### Line 75

```text
 75
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 76–77

```text
 76  -- 26. Recursive CTE creates a 28-day planning calendar
 77  WITH RECURSIVE dates AS(SELECT max(date)+1 AS date,1 AS horizon FROM m5.fact_sales_daily UNION ALL SELECT date+1,horizon+1 FROM dates WHERE horizon<28) SELECT * FROM dates;
```

Question 26: use a recursive CTE to generate exactly 28 dates after final sales. It demonstrates recursion; a calendar table or generate_series is often simpler operationally.


### Line 78

```text
 78
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 79–80

```text
 79  -- 27. Query optimization: inspect actual I/O, not only estimated cost
 80  EXPLAIN (ANALYZE,BUFFERS) SELECT store_id,sum(revenue) FROM m5.fact_sales_daily WHERE date_key BETWEEN 20160101 AND 20160131 GROUP BY store_id;
```

Question 27: EXPLAIN ANALYZE actually executes the read query and reports the plan and buffer use. The fixed historical dates may return few/no rows for a different dataset; adapt them before interpreting performance.


### Line 81

```text
 81
```

Blank separator for readability; no separate executable operation. Within a multiline report string it preserves output spacing.


### Line 82–83

```text
 82  -- 28. Scenario comparison: aggregate each run before averaging
 83  WITH k AS(SELECT policy,run_id,sum(total_inventory_cost) cost FROM m5.fact_inventory_simulation WHERE target_service_level=.95 AND scenario='base' GROUP BY 1,2), p AS(SELECT run_id,max(cost) FILTER(WHERE policy='baseline') baseline,max(cost) FILTER(WHERE policy='optimized') optimized FROM k GROUP BY 1) SELECT avg(baseline-optimized) estimated_cost_reduction,stddev_samp(baseline-optimized) between_run_std FROM p;
```

Question 28: aggregate each policy/run first, pair baseline and alternative within run, then compute average difference and between-run standard deviation. The latter is variability across three default lead-time simulations, not a confidence interval or business-impact proof.


## requirements.txt

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  pandas==2.3.3
```

Tabular manipulation, joins, summaries and dates throughout the smaller-table portions of the pipeline. Version 2.3.3 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 2

```text
  2  numpy==2.2.6
```

Numerical arrays, feature arithmetic, forecast clipping and seeded simulation/fixture randomness. Version 2.2.6 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 3

```text
  3  duckdb==1.4.3
```

Embedded SQL engine for wide-to-long transformation, validation, window features and Parquet exports. Version 1.4.3 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 4

```text
  4  pyarrow==22.0.0
```

Parquet read/write interoperability, schema inspection and bounded database-load batches. Version 22.0.0 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 5

```text
  5  scikit-learn==1.7.2
```

Optional delivery classification, preprocessing pipelines and classification metrics. Version 1.7.2 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 6

```text
  6  lightgbm==4.6.0
```

The global boosted-tree demand candidate and optional delivery-risk classifier. macOS may need an OpenMP runtime. Version 4.6.0 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 7

```text
  7  statsmodels==0.14.6
```

Aggregate ETS/SARIMA diagnostic models; these are not item-store model-selection candidates. Version 0.14.6 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 8

```text
  8  matplotlib==3.10.8
```

Static PNG validation chart generation without a graphical desktop. Version 3.10.8 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 9

```text
  9  plotly==6.5.0
```

Offline-capable interactive model-comparison HTML export. Version 6.5.0 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 10

```text
 10  SQLAlchemy==2.0.45
```

PostgreSQL engine, atomic transaction and table inspection used by the optional serving loader. Version 2.0.45 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 11

```text
 11  psycopg[binary]==3.3.2
```

PostgreSQL driver behind SQLAlchemy; the binary distribution simplifies local installation. Version 3.3.2 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 12

```text
 12  PyYAML==6.0.3
```

Parse project settings/definitions and write the generated YAML field dictionary. Version 6.0.3 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 13

```text
 13  charset-normalizer==3.4.4
```

Detect likely legacy text encoding for DataCo when UTF-8 decoding fails. Version 3.4.4 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 14

```text
 14  python-dotenv==1.2.1
```

Load optional database settings from a locally ignored .env file. Version 1.2.1 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 15

```text
 15  pytest==9.0.2
```

Run unit and integration tests. It is a test dependency included in the main requirements for convenience. Version 9.0.2 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


## requirements-notebooks.txt

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  -r requirements.txt
```

Include the main runtime requirements so a notebook environment has the same project dependencies, then add notebook-specific packages below.


### Line 2

```text
  2  ipykernel==6.30.1
```

Provide the Python execution kernel used by notebooks. Version 6.30.1 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 3

```text
  3  nbclient==0.10.4
```

Execute notebook cells programmatically for validation. Version 0.10.4 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


### Line 4

```text
  4  nbformat==5.10.4
```

Read/write the structured notebook document format. Version 5.10.4 is pinned to reproduce the validated environment, not because all other versions are invalid. Transitive dependencies are not completely locked.


## Makefile

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  .PHONY: install demo sample full test database
```

Declare command targets phony so a file called demo or test will not stop make from executing the task.


### Line 2–3

```text
  2  install:
  3  	python -m pip install -r requirements.txt
```

Provide an install shortcut for pinned runtime dependencies in the active Python environment.


### Line 4–5

```text
  4  demo:
  5  	python src/run_pipeline.py --mode sample --fixture
```

Provide a demo shortcut using explicitly synthetic inputs and sample scope.


### Line 6–7

```text
  6  sample:
  7  	python src/run_pipeline.py --mode sample
```

Provide a real-data sample shortcut; source files must already exist.


### Line 8–9

```text
  8  full:
  9  	python src/run_pipeline.py --mode full
```

Provide a full-data shortcut; training and simulation caps remain in configuration.


### Line 10–11

```text
 10  test:
 11  	python -m pytest -q
```

Provide a pytest shortcut. It does not run the fixture first automatically, so make demo must precede it in a fresh setup.


### Line 12–13

```text
 12  database:
 13  	docker compose up -d --wait
```

Start the optional local PostgreSQL service and wait for its health check. Requires Docker Compose and configured environment password.


## docker-compose.yml

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1–3

```text
  1  services:
  2    postgres:
  3      image: postgres:16.6
```

Define one optional PostgreSQL service with an explicit 16.6 image tag for repeatable local database behavior. Image/runtime availability can change separately from this repository.


### Line 4–7

```text
  4      environment:
  5        POSTGRES_USER: control_tower
  6        POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}
  7        POSTGRES_DB: control_tower
```

Set database user, mandatory environment-supplied password and project database name. The password expression fails early if no password is supplied.


### Line 8

```text
  8      ports: ["127.0.0.1:5432:5432"]
```

Bind port 5432 only on local loopback so this development service is not exposed on all host network interfaces.


### Line 9

```text
  9      volumes: ["postgres_data:/var/lib/postgresql/data"]
```

Persist database contents in a named volume so restarting the container does not automatically erase the database.


### Line 10–13

```text
 10      healthcheck:
 11        test: ["CMD-SHELL", "pg_isready -U control_tower"]
 12        interval: 5s
 13        retries: 10
```

Use pg_isready at five-second intervals for readiness detection; the waiting setup command can then avoid racing server startup.


### Line 14–15

```text
 14  volumes:
 15    postgres_data:
```

Declare the persistent named volume referenced by the service.


## .env.example

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  DATABASE_URL=postgresql+psycopg://control_tower:change_me_local_only@localhost:5432/control_tower
```

Example SQLAlchemy PostgreSQL connection string: driver, user, placeholder password, local host/port and database. Copy to .env and set matching private values only when using PostgreSQL.


### Line 2

```text
  2  POSTGRES_PASSWORD=change_me_local_only
```

Example Docker database password variable; it must match DATABASE_URL's password for the supplied local service. The placeholder is not a real secret.


### Line 3

```text
  3  # Kaggle credentials belong in your personal Kaggle configuration, never this repository.
```

Keep Kaggle authentication in its personal credential mechanism rather than adding it to tracked project source.


## .gitignore

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  .venv/
```

Exclude the local Python virtual environment because it is machine-specific and can be regenerated from requirements.


### Line 2

```text
  2  .env
```

Exclude .env to reduce accidental credential publication. Gitignore does not remove a secret that was already tracked/committed.


### Line 3–6

```text
  3  *.pyc
  4  __pycache__/
  5  .pytest_cache/
  6  .ipynb_checkpoints/
```

Exclude Python bytecode, test caches and notebook checkpoint backups because they are generated intermediates.


### Line 7–9

```text
  7  data/raw/**
  8  !data/raw/**/
  9  !data/raw/**/.gitkeep
```

Exclude raw dataset contents while allowing folder structure and .gitkeep placeholders. Source data licenses/size/privacy should be handled separately from source-code publication.


### Line 10–13

```text
 10  data/interim/**
 11  data/processed/**
 12  data/powerbi/**
 13  !data/**/.gitkeep
```

Exclude intermediate, processed and analytical export files, preserving only empty-folder markers. Users regenerate results through the pipeline.


### Line 14–15

```text
 14  *.duckdb*
 15  *.log
```

Exclude local DuckDB files and logs, which can contain large or environment-specific data.


### Line 16

```text
 16  kaggle.json
```

Exclude the usual Kaggle credential filename as an additional protection; never rely on naming rules as the only secret safeguard.


### Line 17

```text
 17  .DS_Store
```

Exclude macOS Finder metadata unrelated to project behavior.


## docs/github-actions-ci.yml.example

Source snapshot: 0b85891. Related statement lines are grouped below.


### Line 1

```text
  1  name: Validate control tower
```

Name an optional continuous-integration workflow. This file has an .example extension outside .github/workflows, so it is inactive and causes no automated runs.


### Line 2

```text
  2  on: [push, pull_request]
```

If deliberately activated in GitHub's workflow directory, trigger it on pushes and pull requests.


### Line 3–5

```text
  3  jobs:
  4    fixture-and-postgres:
  5      runs-on: ubuntu-latest
```

Define one Linux validation job. ubuntu-latest is a moving runner image, not a fully pinned operating-system environment.


### Line 6–14

```text
  6      services:
  7        postgres:
  8          image: postgres:16.6
  9          env:
 10            POSTGRES_USER: tower_test
 11            POSTGRES_PASSWORD: local_ci_only
 12            POSTGRES_DB: control_tower
 13          ports: ["5432:5432"]
 14          options: --health-cmd pg_isready --health-interval 5s --health-retries 10
```

Start a temporary PostgreSQL 16.6 service with disposable job-only credentials, port mapping and readiness check. local_ci_only is an example temporary test password, not a real account secret.


### Line 15–16

```text
 15      steps:
 16        - uses: actions/checkout@v4
```

Check out repository source into the runner so subsequent commands have the files.


### Line 17–20

```text
 17        - uses: actions/setup-python@v5
 18          with:
 19            python-version: '3.11'
 20            cache: pip
```

Install Python 3.11 and enable pip dependency caching for faster repeat runs.


### Line 21

```text
 21        - run: python -m pip install -r requirements.txt
```

Install pinned project runtime/test dependencies.


### Line 22

```text
 22        - run: python src/run_pipeline.py --mode sample --fixture
```

Generate fixture outputs before tests because integration tests read those files.


### Line 23–25

```text
 23        - run: python -m pytest -q
 24          env:
 25            TEST_DATABASE_URL: postgresql+psycopg://tower_test:local_ci_only@localhost:5432/control_tower
```

Run pytest with TEST_DATABASE_URL so the database test executes rather than skips. This template has not been activated/native-run in this repository.


## notebooks/01_data_audit.ipynb

Source snapshot: 0b85891. Related statement lines are grouped below.


### Cell 2 · Line 1

```text
  1  from pathlib import Path
```

Import filesystem paths for locating exports.


### Cell 2 · Line 2

```text
  2  import pandas as pd
```

Import Pandas for reading Parquet and manipulating result tables.


### Cell 2 · Line 3

```text
  3  ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
```

Resolve the repository root when started either at root or inside notebooks. This is a convenience rule and will not find the project from every arbitrary working directory.


### Cell 2 · Line 4

```text
  4  RUN = 'fixture'
```

Select fixture outputs explicitly so synthetic data are labeled; change to sample/full only after that source run exists.


### Cell 2 · Line 5

```text
  5  OUT = ROOT / 'data/powerbi' / RUN
```

Construct the export directory for the selected run.


### Cell 2 · Line 6

```text
  6  def read(name):
```

Define a reusable table reader by export name.


### Cell 2 · Line 7

```text
  7      return pd.read_parquet(OUT / (name + '.parquet'))
```

Read the corresponding typed Parquet file; this notebook consumes pipeline output rather than retraining models.


### Cell 2 · Line 8

```text
  8  assert OUT.exists(), 'Run python src/run_pipeline.py --mode sample --fixture first'
```

Fail clearly if the pipeline output directory is absent. This checks the directory, not every expected table or freshness.


### Cell 3 · Line 1

```text
  1  import json
```

Import JSON parsing for the generated audit reports.


### Cell 3 · Line 2

```text
  2  audits = [json.loads(p.read_text()) for p in (ROOT / 'reports' / RUN).glob('*_audit.json')]
```

Read every source audit for the selected run, retaining reports rather than rereading private raw values.


### Cell 3 · Line 3

```text
  3  pd.DataFrame([{k: a[k] for k in ['filename','rows','columns','duplicate_rows','encoding']} for a in audits])
```

Display filenames, dimensions, duplicate counts and encoding as a compact input-quality overview.


## notebooks/02_m5_exploratory_analysis.ipynb

Source snapshot: 0b85891. Related statement lines are grouped below.


### Cell 2 · Line 1

```text
  1  from pathlib import Path
```

Import filesystem paths for locating exports.


### Cell 2 · Line 2

```text
  2  import pandas as pd
```

Import Pandas for reading Parquet and manipulating result tables.


### Cell 2 · Line 3

```text
  3  ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
```

Resolve the repository root when started either at root or inside notebooks. This is a convenience rule and will not find the project from every arbitrary working directory.


### Cell 2 · Line 4

```text
  4  RUN = 'fixture'
```

Select fixture outputs explicitly so synthetic data are labeled; change to sample/full only after that source run exists.


### Cell 2 · Line 5

```text
  5  OUT = ROOT / 'data/powerbi' / RUN
```

Construct the export directory for the selected run.


### Cell 2 · Line 6

```text
  6  def read(name):
```

Define a reusable table reader by export name.


### Cell 2 · Line 7

```text
  7      return pd.read_parquet(OUT / (name + '.parquet'))
```

Read the corresponding typed Parquet file; this notebook consumes pipeline output rather than retraining models.


### Cell 2 · Line 8

```text
  8  assert OUT.exists(), 'Run python src/run_pipeline.py --mode sample --fixture first'
```

Fail clearly if the pipeline output directory is absent. This checks the directory, not every expected table or freshness.


### Cell 3 · Line 1

```text
  1  perf = read('product_store_performance')
```

Read current item-store performance summaries.


### Cell 3 · Line 2

```text
  2  display(perf.sort_values('revenue', ascending=False).head(20))
```

Display the top 20 pairs by recent revenue to inspect contribution and ranking.


### Cell 3 · Line 3

```text
  3  read('sales_monthly').plot(x='period', y='revenue', title=RUN + ' | M5 monthly revenue')
```

Plot monthly portfolio revenue to inspect trend/seasonality and large data discontinuities.


### Cell 3 · Line 4

```text
  4  display(read('m5_by_event_name'))
```

Inspect descriptive event-level sales; this does not estimate causal uplift.


### Cell 3 · Line 5

```text
  5  display(read('abc_xyz_segmentation').groupby('abc_xyz').size())
```

Count pairs by ABC-XYZ label to understand the portfolio mix.


## notebooks/03_dataco_operations_analysis.ipynb

Source snapshot: 0b85891. Related statement lines are grouped below.


### Cell 2 · Line 1

```text
  1  from pathlib import Path
```

Import filesystem paths for locating exports.


### Cell 2 · Line 2

```text
  2  import pandas as pd
```

Import Pandas for reading Parquet and manipulating result tables.


### Cell 2 · Line 3

```text
  3  ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
```

Resolve the repository root when started either at root or inside notebooks. This is a convenience rule and will not find the project from every arbitrary working directory.


### Cell 2 · Line 4

```text
  4  RUN = 'fixture'
```

Select fixture outputs explicitly so synthetic data are labeled; change to sample/full only after that source run exists.


### Cell 2 · Line 5

```text
  5  OUT = ROOT / 'data/powerbi' / RUN
```

Construct the export directory for the selected run.


### Cell 2 · Line 6

```text
  6  def read(name):
```

Define a reusable table reader by export name.


### Cell 2 · Line 7

```text
  7      return pd.read_parquet(OUT / (name + '.parquet'))
```

Read the corresponding typed Parquet file; this notebook consumes pipeline output rather than retraining models.


### Cell 2 · Line 8

```text
  8  assert OUT.exists(), 'Run python src/run_pipeline.py --mode sample --fixture first'
```

Fail clearly if the pipeline output directory is absent. This checks the directory, not every expected table or freshness.


### Cell 3 · Line 1

```text
  1  display(read('dataco_shipping_mode_performance'))
```

Display shipping/market/region/segment service summaries; these are alternative grouping dimensions.


### Cell 3 · Line 2

```text
  2  display(read('dataco_profitability_summary').query("dimension == 'category'"))
```

Select category-level profitability from the stacked summary table, avoiding mixtures of overlapping dimensions.


### Cell 3 · Line 3

```text
  3  display(read('dataco_order_profit').query('loss_making_order').sort_values('profit').head(20))
```

List the 20 most negative whole-order profits after line aggregation, not merely loss-making lines.


## notebooks/04_demand_forecasting.ipynb

Source snapshot: 0b85891. Related statement lines are grouped below.


### Cell 2 · Line 1

```text
  1  from pathlib import Path
```

Import filesystem paths for locating exports.


### Cell 2 · Line 2

```text
  2  import pandas as pd
```

Import Pandas for reading Parquet and manipulating result tables.


### Cell 2 · Line 3

```text
  3  ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
```

Resolve the repository root when started either at root or inside notebooks. This is a convenience rule and will not find the project from every arbitrary working directory.


### Cell 2 · Line 4

```text
  4  RUN = 'fixture'
```

Select fixture outputs explicitly so synthetic data are labeled; change to sample/full only after that source run exists.


### Cell 2 · Line 5

```text
  5  OUT = ROOT / 'data/powerbi' / RUN
```

Construct the export directory for the selected run.


### Cell 2 · Line 6

```text
  6  def read(name):
```

Define a reusable table reader by export name.


### Cell 2 · Line 7

```text
  7      return pd.read_parquet(OUT / (name + '.parquet'))
```

Read the corresponding typed Parquet file; this notebook consumes pipeline output rather than retraining models.


### Cell 2 · Line 8

```text
  8  assert OUT.exists(), 'Run python src/run_pipeline.py --mode sample --fixture first'
```

Fail clearly if the pipeline output directory is absent. This checks the directory, not every expected table or freshness.


### Cell 3 · Line 1

```text
  1  display(read('forecast_model_metrics'))
```

Display every model/fold/forecast-level metric; compare candidates only at matching levels.


### Cell 3 · Line 2

```text
  2  f = read('forecast_backtest_selected')
```

Read the chosen model’s independent final-test rows.


### Cell 3 · Line 3

```text
  3  f.groupby('date')[['actual_units','forecast_units']].sum().plot(title=RUN + ' | locked test')
```

Aggregate matched actual/forecast units by date and plot them; good portfolio fit can still hide pair-level errors.


### Cell 3 · Line 4

```text
  4  display(read('forecast_accuracy_by_segment'))
```

Inspect errors by store/category/volume/ABC-XYZ to find weak segments.


### Cell 3 · Line 5

```text
  5  display(read('demand_forecasts_28d').head())
```

Inspect future prediction rows separately from held-out backtest predictions.


## notebooks/05_inventory_optimization.ipynb

Source snapshot: 0b85891. Related statement lines are grouped below.


### Cell 2 · Line 1

```text
  1  from pathlib import Path
```

Import filesystem paths for locating exports.


### Cell 2 · Line 2

```text
  2  import pandas as pd
```

Import Pandas for reading Parquet and manipulating result tables.


### Cell 2 · Line 3

```text
  3  ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
```

Resolve the repository root when started either at root or inside notebooks. This is a convenience rule and will not find the project from every arbitrary working directory.


### Cell 2 · Line 4

```text
  4  RUN = 'fixture'
```

Select fixture outputs explicitly so synthetic data are labeled; change to sample/full only after that source run exists.


### Cell 2 · Line 5

```text
  5  OUT = ROOT / 'data/powerbi' / RUN
```

Construct the export directory for the selected run.


### Cell 2 · Line 6

```text
  6  def read(name):
```

Define a reusable table reader by export name.


### Cell 2 · Line 7

```text
  7      return pd.read_parquet(OUT / (name + '.parquet'))
```

Read the corresponding typed Parquet file; this notebook consumes pipeline output rather than retraining models.


### Cell 2 · Line 8

```text
  8  assert OUT.exists(), 'Run python src/run_pipeline.py --mode sample --fixture first'
```

Fail clearly if the pipeline output directory is absent. This checks the directory, not every expected table or freshness.


### Cell 3 · Line 1

```text
  1  display(read('inventory_assumptions').head())
```

Inspect assumed inventory inputs before interpreting policy outcomes.


### Cell 3 · Line 2

```text
  2  k = read('inventory_simulation_kpis').query('target_service_level == 0.95')
```

Choose 95% service so alternative service worlds are not added together.


### Cell 3 · Line 3

```text
  3  display(k.groupby(['policy','run_id'])[['total_inventory_cost','lost_sales_units']].sum().groupby('policy').mean())
```

Sum cost/lost units per policy/run, then average runs to obtain a portfolio policy comparison.


### Cell 3 · Line 4

```text
  4  display(read('inventory_sensitivity').groupby(['scenario','policy','target_service_level']).total_inventory_cost.mean())
```

Summarize sensitivity by scenario/policy/service. This expression averages pair-run cost rows; it is a mean per pair/run, not the portfolio total used in the preceding line. Align aggregation before comparing the two.


## notebooks/06_executive_findings.ipynb

Source snapshot: 0b85891. Related statement lines are grouped below.


### Cell 2 · Line 1

```text
  1  from pathlib import Path
```

Import filesystem paths for locating exports.


### Cell 2 · Line 2

```text
  2  import pandas as pd
```

Import Pandas for reading Parquet and manipulating result tables.


### Cell 2 · Line 3

```text
  3  ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
```

Resolve the repository root when started either at root or inside notebooks. This is a convenience rule and will not find the project from every arbitrary working directory.


### Cell 2 · Line 4

```text
  4  RUN = 'fixture'
```

Select fixture outputs explicitly so synthetic data are labeled; change to sample/full only after that source run exists.


### Cell 2 · Line 5

```text
  5  OUT = ROOT / 'data/powerbi' / RUN
```

Construct the export directory for the selected run.


### Cell 2 · Line 6

```text
  6  def read(name):
```

Define a reusable table reader by export name.


### Cell 2 · Line 7

```text
  7      return pd.read_parquet(OUT / (name + '.parquet'))
```

Read the corresponding typed Parquet file; this notebook consumes pipeline output rather than retraining models.


### Cell 2 · Line 8

```text
  8  assert OUT.exists(), 'Run python src/run_pipeline.py --mode sample --fixture first'
```

Fail clearly if the pipeline output directory is absent. This checks the directory, not every expected table or freshness.


### Cell 3 · Line 1

```text
  1  from IPython.display import Markdown
```

Import rich Markdown rendering for a readable generated report.


### Cell 3 · Line 2

```text
  2  display(read('executive_kpis'))
```

Display executive metrics with domain/type/provenance labels; do not sum unlike metrics.


### Cell 3 · Line 3

```text
  3  display(Markdown((ROOT / 'reports' / RUN / 'executive_summary.md').read_text()))
```

Read and render the evidence report for the selected output run.


## powerbi/dax_measures.md

Source snapshot: 0b85891. Related statement lines are grouped below.


### Total Units Sold · Line 6

```text
  6  Total Units Sold =
```

Define the measure name shown in Power BI. Sum additive daily units after dimension filtering; summing already-aggregated overlapping tables would double count.


### Total Units Sold · Line 7

```text
  7  SUM(sales_daily[units_sold])
```

Evaluate the formula under the current dashboard filter context. Sum additive daily units after dimension filtering; summing already-aggregated overlapping tables would double count.


### Total Revenue · Line 17

```text
 17  Total Revenue =
```

Define the measure name shown in Power BI. Sum the precomputed units×weekly-price proxy. It is source-domain revenue, not a combined cross-dataset financial total.


### Total Revenue · Line 18

```text
 18  SUM(sales_daily[revenue])
```

Evaluate the formula under the current dashboard filter context. Sum the precomputed units×weekly-price proxy. It is source-domain revenue, not a combined cross-dataset financial total.


### Average Selling Price · Line 28

```text
 28  Average Selling Price =
```

Define the measure name shown in Power BI. Revenue/units gives a quantity-weighted price. Averaging row prices would weight low-volume and high-volume rows equally.


### Average Selling Price · Line 29

```text
 29  DIVIDE([Total Revenue], [Total Units Sold])
```

Evaluate the formula under the current dashboard filter context. Revenue/units gives a quantity-weighted price. Averaging row prices would weight low-volume and high-volume rows equally.


### Revenue Previous Period · Line 39

```text
 39  Revenue Previous Period =
```

Define the measure name shown in Power BI. Shift the selected date context one month with DATEADD, then recalculate revenue. It requires a suitable date table/relationship and comparable date selections.


### Revenue Previous Period · Line 40

```text
 40  CALCULATE([Total Revenue], DATEADD(dim_date[date], -1, MONTH))
```

Evaluate the formula under the current dashboard filter context. Shift the selected date context one month with DATEADD, then recalculate revenue. It requires a suitable date table/relationship and comparable date selections.


### Revenue Growth % · Line 50

```text
 50  Revenue Growth % =
```

Define the measure name shown in Power BI. Compare change with the prior-period base, returning blank for an unavailable/zero base rather than an invented growth rate.


### Revenue Growth % · Line 51

```text
 51  DIVIDE([Total Revenue] - [Revenue Previous Period], [Revenue Previous Period])
```

Evaluate the formula under the current dashboard filter context. Compare change with the prior-period base, returning blank for an unavailable/zero base rather than an invented growth rate.


### Forecast Units · Line 61

```text
 61  Forecast Units =
```

Define the measure name shown in Power BI. Sum the selected-model future snapshot. Forecast dates may be outside the historical slicer range, legitimately producing a blank visual.


### Forecast Units · Line 62

```text
 62  SUM(demand_forecasts_28d[forecast_units])
```

Evaluate the formula under the current dashboard filter context. Sum the selected-model future snapshot. Forecast dates may be outside the historical slicer range, legitimately producing a blank visual.


### Actual Units · Line 72

```text
 72  Actual Units =
```

Define the measure name shown in Power BI. Use the matched locked-test table, so forecast errors and the denominator refer to the same dates and selected series.


### Actual Units · Line 73

```text
 73  SUM(forecast_backtest_selected[actual_units])
```

Evaluate the formula under the current dashboard filter context. Use the matched locked-test table, so forecast errors and the denominator refer to the same dates and selected series.


### Forecast Error · Line 83

```text
 83  Forecast Error =
```

Define the measure name shown in Power BI. Sum signed errors to show net over/underforecasting. Positive and negative errors cancel intentionally for bias.


### Forecast Error · Line 84

```text
 84  SUM(forecast_backtest_selected[error])
```

Evaluate the formula under the current dashboard filter context. Sum signed errors to show net over/underforecasting. Positive and negative errors cancel intentionally for bias.


### Absolute Forecast Error · Line 94

```text
 94  Absolute Forecast Error =
```

Define the measure name shown in Power BI. Sum row-level absolute errors before aggregation so over/underprediction cannot cancel and disguise mistakes.


### Absolute Forecast Error · Line 95

```text
 95  SUM(forecast_backtest_selected[absolute_error])
```

Evaluate the formula under the current dashboard filter context. Sum row-level absolute errors before aggregation so over/underprediction cannot cancel and disguise mistakes.


### Forecast WAPE · Line 105

```text
105  Forecast WAPE =
```

Define the measure name shown in Power BI. Divide aggregate absolute error by matched actual units, rather than averaging individual percentages.


### Forecast WAPE · Line 106

```text
106  DIVIDE([Absolute Forecast Error], [Actual Units])
```

Evaluate the formula under the current dashboard filter context. Divide aggregate absolute error by matched actual units, rather than averaging individual percentages.


### Forecast Bias · Line 116

```text
116  Forecast Bias =
```

Define the measure name shown in Power BI. Divide signed aggregate error by actual volume; this is direction of error, not total error magnitude.


### Forecast Bias · Line 117

```text
117  DIVIDE([Forecast Error], [Actual Units])
```

Evaluate the formula under the current dashboard filter context. Divide signed aggregate error by actual volume; this is direction of error, not total error magnitude.


### Scenario Ready · Line 127

```text
127  Scenario Ready =
```

Define the measure name shown in Power BI. Require a single service, policy and scenario selection. A numeric result combining incompatible simulated worlds would be misleading.


### Scenario Ready · Line 128

```text
128  IF(HASONEVALUE(ServiceLevel[value]) && HASONEVALUE(Policy[name]) && HASONEVALUE(Scenario[name]), 1, 0)
```

Evaluate the formula under the current dashboard filter context. Require a single service, policy and scenario selection. A numeric result combining incompatible simulated worlds would be misleading.


### Inventory Value · Line 138

```text
138  Inventory Value =
```

Define the measure name shown in Power BI. Allow one service slice before summing repeated starting-stock investment, preventing triple counting across alternative targets.


### Inventory Value · Line 139

```text
139  IF(HASONEVALUE(ServiceLevel[value]), SUM(inventory_policy_recommendations[inventory_value]))
```

Evaluate the formula under the current dashboard filter context. Allow one service slice before summing repeated starting-stock investment, preventing triple counting across alternative targets.


### Safety Stock Units · Line 149

```text
149  Safety Stock Units =
```

Define the measure name shown in Power BI. Sum pair buffers only within one service level. This is a sum of independent recommendations, not an optimized pooled warehouse buffer.


### Safety Stock Units · Line 150

```text
150  IF(HASONEVALUE(ServiceLevel[value]), SUM(inventory_policy_recommendations[safety_stock]))
```

Evaluate the formula under the current dashboard filter context. Sum pair buffers only within one service level. This is a sum of independent recommendations, not an optimized pooled warehouse buffer.


### Reorder Point Units · Line 160

```text
160  Reorder Point Units =
```

Define the measure name shown in Power BI. Sum pair-specific reorder thresholds within one service slice for a portfolio summary; individual ordering still occurs at pair grain.


### Reorder Point Units · Line 161

```text
161  IF(HASONEVALUE(ServiceLevel[value]), SUM(inventory_policy_recommendations[reorder_point]))
```

Evaluate the formula under the current dashboard filter context. Sum pair-specific reorder thresholds within one service slice for a portfolio summary; individual ordering still occurs at pair grain.


### EOQ Units · Line 171

```text
171  EOQ Units =
```

Define the measure name shown in Power BI. Sum economic-lot recommendations within one service slice. This total is descriptive and is not one universal order quantity.


### EOQ Units · Line 172

```text
172  IF(HASONEVALUE(ServiceLevel[value]), SUM(inventory_policy_recommendations[eoq]))
```

Evaluate the formula under the current dashboard filter context. Sum economic-lot recommendations within one service slice. This total is descriptive and is not one universal order quantity.


### Estimated Excess Inventory · Line 182

```text
182  Estimated Excess Inventory =
```

Define the measure name shown in Power BI. Sum assumed excess value against the modeled protection target for one service level; do not call it verified obsolete inventory.


### Estimated Excess Inventory · Line 183

```text
183  IF(HASONEVALUE(ServiceLevel[value]), SUM(inventory_policy_recommendations[excess_value]))
```

Evaluate the formula under the current dashboard filter context. Sum assumed excess value against the modeled protection target for one service level; do not call it verified obsolete inventory.


### Days of Supply · Line 193

```text
193  Days of Supply =
```

Define the measure name shown in Power BI. Divide portfolio opening units by portfolio daily forecast, not a sum or unweighted average of pair days-of-supply ratios.


### Days of Supply · Line 194

```text
194  IF(HASONEVALUE(ServiceLevel[value]), DIVIDE(SUM(inventory_policy_recommendations[initial_inventory]), SUM(inventory_policy_recommendations[forecast_daily_demand])))
```

Evaluate the formula under the current dashboard filter context. Divide portfolio opening units by portfolio daily forecast, not a sum or unweighted average of pair days-of-supply ratios.


### Products at Stockout Risk · Line 204

```text
204  Products at Stockout Risk =
```

Define the measure name shown in Power BI. Filter on probability > tolerated 1−target risk and count rows. Despite the name this counts item-store pairs, not unique product IDs.


### Products at Stockout Risk · Line 205

```text
205  IF(HASONEVALUE(ServiceLevel[value]), COUNTROWS(FILTER(inventory_policy_recommendations, inventory_policy_recommendations[stockout_probability] > 1 - inventory_policy_recommendations[target_service_level])))
```

Evaluate the formula under the current dashboard filter context. Filter on probability > tolerated 1−target risk and count rows. Despite the name this counts item-store pairs, not unique product IDs.


### Stockout Events · Line 215

```text
215  Stockout Events =
```

Define the measure name shown in Power BI. Sum shortage events within each run then average runs. The unit is item-store-days with lost demand, not unique affected products.


### Stockout Events · Line 216

```text
216  IF([Scenario Ready] = 1, AVERAGEX(VALUES(inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[stockout_event]))))
```

Evaluate the formula under the current dashboard filter context. Sum shortage events within each run then average runs. The unit is item-store-days with lost demand, not unique affected products.


### Lost Sales Units · Line 226

```text
226  Lost Sales Units =
```

Define the measure name shown in Power BI. Average per-run total unfilled units rather than treating repeated demand paths as additive actual demand.


### Lost Sales Units · Line 227

```text
227  IF([Scenario Ready] = 1, AVERAGEX(VALUES(inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[lost_sales_units]))))
```

Evaluate the formula under the current dashboard filter context. Average per-run total unfilled units rather than treating repeated demand paths as additive actual demand.


### Lost Sales Value · Line 237

```text
237  Lost Sales Value =
```

Define the measure name shown in Power BI. Average per-run price-valued lost units. This differs from lost-sale penalty included in inventory cost.


### Lost Sales Value · Line 238

```text
238  IF([Scenario Ready] = 1, AVERAGEX(VALUES(inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[lost_sales_value]))))
```

Evaluate the formula under the current dashboard filter context. Average per-run price-valued lost units. This differs from lost-sale penalty included in inventory cost.


### Total Holding Cost · Line 248

```text
248  Total Holding Cost =
```

Define the measure name shown in Power BI. Average simulated carrying cost across runs after summing each world; preserve service/policy/scenario filters.


### Total Holding Cost · Line 249

```text
249  IF([Scenario Ready] = 1, AVERAGEX(VALUES(inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[holding_cost]))))
```

Evaluate the formula under the current dashboard filter context. Average simulated carrying cost across runs after summing each world; preserve service/policy/scenario filters.


### Total Ordering Cost · Line 259

```text
259  Total Ordering Cost =
```

Define the measure name shown in Power BI. Average total fixed placed-order costs across repeated worlds. Receipt timing does not change when this simulator charges the order cost.


### Total Ordering Cost · Line 260

```text
260  IF([Scenario Ready] = 1, AVERAGEX(VALUES(inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[ordering_cost]))))
```

Evaluate the formula under the current dashboard filter context. Average total fixed placed-order costs across repeated worlds. Receipt timing does not change when this simulator charges the order cost.


### Total Inventory Cost · Line 270

```text
270  Total Inventory Cost =
```

Define the measure name shown in Power BI. Average each run’s holding+ordering+lost-penalty total. Purchase expenditure and other unmodeled costs are excluded.


### Total Inventory Cost · Line 271

```text
271  IF([Scenario Ready] = 1, AVERAGEX(VALUES(inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[total_inventory_cost]))))
```

Evaluate the formula under the current dashboard filter context. Average each run’s holding+ordering+lost-penalty total. Purchase expenditure and other unmodeled costs are excluded.


### Stockout Rate · Line 281

```text
281  Stockout Rate =
```

Define the measure name shown in Power BI. Divide stockout events by all simulated pair-days. Pooling runs is appropriate for this denominator-weighted event rate with matching grids.


### Stockout Rate · Line 282

```text
282  IF([Scenario Ready] = 1, DIVIDE(SUM(inventory_simulation_daily[stockout_event]), COUNTROWS(inventory_simulation_daily)))
```

Evaluate the formula under the current dashboard filter context. Divide stockout events by all simulated pair-days. Pooling runs is appropriate for this denominator-weighted event rate with matching grids.


### Fill Rate · Line 292

```text
292  Fill Rate =
```

Define the measure name shown in Power BI. Divide total fulfilled by total requested units; this retains demand weighting and is different from averaging per-item percentages.


### Fill Rate · Line 293

```text
293  IF([Scenario Ready] = 1, DIVIDE(SUM(inventory_simulation_daily[fulfilled_units]), SUM(inventory_simulation_daily[actual_demand])))
```

Evaluate the formula under the current dashboard filter context. Divide total fulfilled by total requested units; this retains demand weighting and is different from averaging per-item percentages.


### Average Inventory · Line 303

```text
303  Average Inventory =
```

Define the measure name shown in Power BI. First group by date/run, sum the entire portfolio inside each group, then average groups. A plain row average would return average item inventory instead of portfolio inventory.


### Average Inventory · Line 304

```text
304  IF([Scenario Ready] = 1, AVERAGEX(SUMMARIZE(inventory_simulation_daily, inventory_simulation_daily[date], inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[closing_inventory]))))
```

Evaluate the formula under the current dashboard filter context. First group by date/run, sum the entire portfolio inside each group, then average groups. A plain row average would return average item inventory instead of portfolio inventory.


### Inventory Turnover · Line 314

```text
314  Inventory Turnover =
```

Define the measure name shown in Power BI. Average fulfilled portfolio units across runs, divide by average portfolio inventory and annualize by observed days. VAR holds intermediate values; this is a unit proxy rather than COGS-based financial turnover.


### Inventory Turnover · Line 315

```text
315  VAR Fulfilled = AVERAGEX(VALUES(inventory_simulation_daily[run_id]), CALCULATE(SUM(inventory_simulation_daily[fulfilled_units]))) VAR Days = DISTINCTCOUNT(inventory_simulation_daily[date]) RETURN IF([Scenario Ready] = 1, DIVIDE(Fulfilled, [Average Inventory]) * DIVIDE(365, Days))
```

Evaluate the formula under the current dashboard filter context. Average fulfilled portfolio units across runs, divide by average portfolio inventory and annualize by observed days. VAR holds intermediate values; this is a unit proxy rather than COGS-based financial turnover.


### Baseline Inventory Cost · Line 325

```text
325  Baseline Inventory Cost =
```

Define the measure name shown in Power BI. Remove the current Policy filter and impose baseline while keeping the matched service/scenario and other dimensions.


### Baseline Inventory Cost · Line 326

```text
326  CALCULATE([Total Inventory Cost], REMOVEFILTERS(Policy), Policy[name] = "baseline")
```

Evaluate the formula under the current dashboard filter context. Remove the current Policy filter and impose baseline while keeping the matched service/scenario and other dimensions.


### Optimized Inventory Cost · Line 336

```text
336  Optimized Inventory Cost =
```

Define the measure name shown in Power BI. Apply the same context but force the forecast-based policy. Calling it optimized does not establish global optimality.


### Optimized Inventory Cost · Line 337

```text
337  CALCULATE([Total Inventory Cost], REMOVEFILTERS(Policy), Policy[name] = "optimized")
```

Evaluate the formula under the current dashboard filter context. Apply the same context but force the forecast-based policy. Calling it optimized does not establish global optimality.


### Estimated Cost Reduction · Line 347

```text
347  Estimated Cost Reduction =
```

Define the measure name shown in Power BI. Subtract matched alternative cost from baseline. Retain negative values to reveal deterioration.


### Estimated Cost Reduction · Line 348

```text
348  [Baseline Inventory Cost] - [Optimized Inventory Cost]
```

Evaluate the formula under the current dashboard filter context. Subtract matched alternative cost from baseline. Retain negative values to reveal deterioration.


### Estimated Cost Reduction % · Line 358

```text
358  Estimated Cost Reduction % =
```

Define the measure name shown in Power BI. Scale the difference by baseline cost; zero/unknown baseline means undefined percentage.


### Estimated Cost Reduction % · Line 359

```text
359  DIVIDE([Estimated Cost Reduction], [Baseline Inventory Cost])
```

Evaluate the formula under the current dashboard filter context. Scale the difference by baseline cost; zero/unknown baseline means undefined percentage.


### Total Orders · Line 369

```text
369  Total Orders =
```

Define the measure name shown in Power BI. Count distinct order IDs in the order-grain table; category filtering is handled explicitly by a separate measure.


### Total Orders · Line 370

```text
370  DISTINCTCOUNT(dataco_delivery_performance[order_id])
```

Evaluate the formula under the current dashboard filter context. Count distinct order IDs in the order-grain table; category filtering is handled explicitly by a separate measure.


### Eligible Orders · Line 380

```text
380  Eligible Orders =
```

Define the measure name shown in Power BI. Modify context to orders with valid durations/status so the late-rate denominator is defensible.


### Eligible Orders · Line 381

```text
381  CALCULATE([Total Orders], dataco_delivery_performance[delivery_eligible] = TRUE())
```

Evaluate the formula under the current dashboard filter context. Modify context to orders with valid durations/status so the late-rate denominator is defensible.


### Late Orders · Line 391

```text
391  Late Orders =
```

Define the measure name shown in Power BI. Require both eligibility and late flag, counting unique orders instead of lines.


### Late Orders · Line 392

```text
392  CALCULATE([Total Orders], dataco_delivery_performance[delivery_eligible] = TRUE(), dataco_delivery_performance[late_order] = 1)
```

Evaluate the formula under the current dashboard filter context. Require both eligibility and late flag, counting unique orders instead of lines.


### Late Delivery % · Line 402

```text
402  Late Delivery % =
```

Define the measure name shown in Power BI. Use late/eligible on the same scope. Orders lacking valid outcome information are not on-time successes.


### Late Delivery % · Line 403

```text
403  DIVIDE([Late Orders], [Eligible Orders])
```

Evaluate the formula under the current dashboard filter context. Use late/eligible on the same scope. Orders lacking valid outcome information are not on-time successes.


### On-Time Delivery % · Line 413

```text
413  On-Time Delivery % =
```

Define the measure name shown in Power BI. Take the complement only with a nonempty eligible denominator; otherwise leave it blank.


### On-Time Delivery % · Line 414

```text
414  IF([Eligible Orders] > 0, 1 - [Late Delivery %])
```

Evaluate the formula under the current dashboard filter context. Take the complement only with a nonempty eligible denominator; otherwise leave it blank.


### Average Delay Days · Line 424

```text
424  Average Delay Days =
```

Define the measure name shown in Power BI. Average positive-only delay for all eligible orders including punctual zeros; it is not mean delay among late orders alone.


### Average Delay Days · Line 425

```text
425  CALCULATE(AVERAGE(dataco_delivery_performance[positive_delay_days]), dataco_delivery_performance[delivery_eligible] = TRUE())
```

Evaluate the formula under the current dashboard filter context. Average positive-only delay for all eligible orders including punctual zeros; it is not mean delay among late orders alone.


### Total Sales · Line 435

```text
435  Total Sales =
```

Define the measure name shown in Power BI. Exclude explicitly invalid sales/quantity rows before adding configured line net sales. This measure relies on the exported DataCo table, whose name differs from the narrow SQL profitability extension.


### Total Sales · Line 436

```text
436  CALCULATE(SUM(dataco_profitability[sales]), dataco_profitability[invalid_sales_flag] = FALSE())
```

Evaluate the formula under the current dashboard filter context. Exclude explicitly invalid sales/quantity rows before adding configured line net sales. This measure relies on the exported DataCo table, whose name differs from the narrow SQL profitability extension.


### Total Profit · Line 446

```text
446  Total Profit =
```

Define the measure name shown in Power BI. Apply the same valid-sales scope as the sales denominator. Abnormal-profit flags remain review items rather than automatic deletions.


### Total Profit · Line 447

```text
447  CALCULATE(SUM(dataco_profitability[profit]), dataco_profitability[invalid_sales_flag] = FALSE())
```

Evaluate the formula under the current dashboard filter context. Apply the same valid-sales scope as the sales denominator. Abnormal-profit flags remain review items rather than automatic deletions.


### Profit Margin % · Line 457

```text
457  Profit Margin % =
```

Define the measure name shown in Power BI. Use ratio of sums so each unit of sales carries appropriate weight, unlike an unweighted mean of line margins.


### Profit Margin % · Line 458

```text
458  DIVIDE([Total Profit], [Total Sales])
```

Evaluate the formula under the current dashboard filter context. Use ratio of sums so each unit of sales carries appropriate weight, unlike an unweighted mean of line margins.


### Loss-Making Orders · Line 468

```text
468  Loss-Making Orders =
```

Define the measure name shown in Power BI. Iterate distinct orders and evaluate summed valid profit in the current filter scope; a category-filtered order result is not necessarily its complete-order outcome.


### Loss-Making Orders · Line 469

```text
469  COUNTROWS(FILTER(VALUES(dataco_profitability[order_id]), CALCULATE([Total Profit]) < 0))
```

Evaluate the formula under the current dashboard filter context. Iterate distinct orders and evaluate summed valid profit in the current filter scope; a category-filtered order result is not necessarily its complete-order outcome.


### Category Late Delivery % · Line 479

```text
479  Category Late Delivery % =
```

Define the measure name shown in Power BI. Get distinct order IDs represented by selected category lines, then TREATAS applies that set to the delivery fact. Multi-category orders can appear in several category rows, so those counts are not additive.


### Category Late Delivery % · Line 480

```text
480  VAR OrdersInCategory = VALUES(dataco_profitability[order_id]) RETURN CALCULATE([Late Delivery %], TREATAS(OrdersInCategory, dataco_delivery_performance[order_id]))
```

Evaluate the formula under the current dashboard filter context. Get distinct order IDs represented by selected category lines, then TREATAS applies that set to the delivery fact. Multi-category orders can appear in several category rows, so those counts are not additive.


### Last Refresh Date · Line 490

```text
490  Last Refresh Date =
```

Define the measure name shown in Power BI. Read the recorded pipeline timestamp; NOW() would show viewing time and could falsely suggest fresh data.


### Last Refresh Date · Line 491

```text
491  MAX(refresh_metadata[last_refresh_utc])
```

Evaluate the formula under the current dashboard filter context. Read the recorded pipeline timestamp; NOW() would show viewing time and could falsely suggest fresh data.


### Dynamic Demand Title · Line 501

```text
501  Dynamic Demand Title =
```

Define the measure name shown in Power BI. Build a label with one selected store or a plural fallback. COALESCE supplies text when SELECTEDVALUE is blank for multiple/no store values.


### Dynamic Demand Title · Line 502

```text
502  "Demand forecast | " & COALESCE(SELECTEDVALUE(dim_store[store_id]), "Selected stores") & " | 28 days"
```

Evaluate the formula under the current dashboard filter context. Build a label with one selected store or a plural fallback. COALESCE supplies text when SELECTEDVALUE is blank for multiple/no store values.
