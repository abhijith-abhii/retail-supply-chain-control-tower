# Verification status

Verified locally using Python 3.12.14, pinned direct dependencies, macOS and a temporary PostgreSQL 18.4 server. Docker configuration targets PostgreSQL 16.6; that exact Docker image was not run here.

| Acceptance area | Executed result |
|---|---|
| Sample pipeline | Passed with explicit synthetic fixture; all raw fixture files audited |
| Sales transform | 14,400 daily rows, 24 item-store series, 600 days |
| Forecasts | 672 production rows = 24 series × 28 days; five item-level candidate models across three chronological folds; two aggregate statistical diagnostics |
| Python + PostgreSQL tests | 19 passed, including loading and integrity checks; no skipped tests in final combined run |
| SQL analyses | All 28 executed successfully; results recorded in sql_validation.json |
| SQL data quality | All 12 failure counts zero on fixture-loaded database |
| Optional risk classifiers | Logistic regression, tree, random forest and LightGBM executed; finite metrics exported in fixture/optional_risk |
| 90-day / full code path | Passed on all 36 synthetic series, 21,600 sales rows, 1,008 future forecast rows; simulation capped at 4 series, 2 runs, audit skipped for this secondary experiment |
| Inventory scenarios | Three service levels, paired baseline/optimized replay, all seven requested sensitivity factors including service level |
| Output dictionary | Generated from actual exported schemas with explicit field definitions and provenance |
| Chart | Forecast validation PNG visually inspected; Plotly comparison HTML generated |
| Notebook verification | All six notebooks executed successfully; 12 code cells, no error outputs; see notebook_validation.json |
| Real Kaggle sample/full | Pending: source files were not supplied or downloaded |
| Power BI Desktop / DAX / PBIX | Specifications supplied; native execution and six-page screenshots remain pending |
| GitHub CI | Workflow provided, not executed on GitHub or published |

No fixture result is a finding about Walmart or DataCo. Full-mode code was exercised on synthetic data, not at complete M5 scale. Historical replay costs are scenario estimates, not achieved savings.

The fixture held-out interval coverage falls below the nominal targets. The report retains that result; do not claim calibrated 80%/95% coverage. Improve residual calibration before operational use.

The local LightGBM OpenMP dependency was satisfied using scikit-learn's bundled libomp.dylib through DYLD_LIBRARY_PATH. Matplotlib used a writable temporary cache. PostgreSQL was isolated in the workspace and stopped after validation; its test binaries and database are not included in this deliverable.
