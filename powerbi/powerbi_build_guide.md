# Reproducible Power BI build

Power BI Desktop on Windows is required for authoring a `.pbix`. This repository supplies specifications and data, not an unverified PBIX.

1. Execute the sample pipeline; choose fixture only for engineering demonstration. Record `run_manifest.json` and the export folder. Download both licensed datasets separately for real findings.
2. Open Desktop → Get Data → PostgreSQL, or use Folder for CSV exports and the Parquet connector for sales_daily. Define a `DataFolder` parameter. Import each named table separately; do not concatenate unrelated CSV files through Combine Files.
3. For Parquet use a Power Query such as `Parquet.Document(File.Contents(DataFolder & "/sales_daily.parquet"))`. For CSV use `Table.PromoteHeaders(Csv.Document(File.Contents(DataFolder & "/demand_forecasts_28d.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]))`, then explicitly apply schema types from the dictionary. Local gateway paths must be accessible to the gateway service account.
4. Import dimensions and the two fact domains from data_model.md. Remove automatic relationships. Set date fields to Date, IDs to Text (order IDs whole numbers), flags to Boolean where appropriate. Set date table. Enrich product/store dimensions in Power Query if needed.
5. Set up the documented single-direction relationships and selector tables. Hide technical fields and disable implicit summarization for numeric IDs. Put every explicit measure into `_Measures`; copy DAX from dax_measures.md in dependency order.
6. Import dashboard_theme.json. Build the six pages from dashboard_wireframes.md, then the hidden detail/tooltip pages. Configure single-select scenario controls with 95% / optimized / base defaults. Add refresh/provenance captions and reset bookmarks.
7. Reconcile M5 sales with SQL query 1, selected-model WAPE with query 14, simulated costs with query 28 and DataCo late rates with query 19. Check blank denominators, a single product/store, multi-category orders, and all-store totals. Verify that switching M5 store does not alter DataCo values.
8. Set product-store interval visuals to one item and store; portfolio band sums are not statistically valid. Inventory snapshots must not change with historical day slicers. Costs must average runs, not add them.
9. Save as RetailSupplyChainControlTower.pbix. For publishing use a workspace with least-privilege read-only database access and gateway credentials managed in Power BI Service. Never embed source passwords in M scripts or Git. Configure refresh after the Python pipeline finishes atomically.
10. Export six screenshots and record Desktop version, source run ID, reconciliation totals and refresh time in reports/powerbi_validation.md. Until this is done, native Power BI validation remains pending.

## Performance
Use Import mode for the sample. For full data, incremental refresh on date and PostgreSQL monthly aggregation marts may be preferable. Keep high-cardinality item IDs off executive visuals. Do not import raw DataCo files. Profile slow visuals with Performance Analyzer before adding bidirectional filters.

## Publishing checklist
Actual findings, forecast results and simulated scenarios must remain visibly distinct. M5 contains observed sales rather than unconstrained demand; SNAP is not a promotion flag. Operational decomposition is associative. Real deployment requires source ownership, scheduled orchestration, monitoring and real inventory feeds.
