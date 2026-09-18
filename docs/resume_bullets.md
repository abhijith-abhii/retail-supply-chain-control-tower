# Resume bullets

- Built an end-to-end retail supply-chain analytics prototype using Python, PostgreSQL, DuckDB and Parquet to forecast 28-day product-store demand, with a six-page Power BI model and dashboard specification.
- Developed baseline and global LightGBM forecasting pipelines with lag, rolling-demand, price, event and calendar features, using chronological backtests and MAE, RMSE, WAPE, RMSSE and bias diagnostics.
- Designed configurable safety-stock, reorder-point, EOQ and paired inventory simulations, while modeling independent DataCo delivery and profit measures with privacy safeguards and explicit scenario assumptions.

Use “built Power BI dashboard” only after implementing and validating the PBIX. Do not claim measured real-world savings. After a real run, replace generic scale with manifest source_sales_rows and distinct item-store count, test WAPE from forecast_model_metrics, and clearly labelled simulated cost differences from inventory_simulation_kpis. Synthetic validation counts can be described as tests, never as retailer findings.
