# Architecture and grains

```mermaid
flowchart TD
 A[M5 raw CSV] --> V[Schema and quality audit]
 B[DataCo raw CSV] --> P[Allowlist and PII removal]
 V --> D[DuckDB unpivot and joins]
 D --> Q[Store/year Parquet]
 P --> O[Independent order and line facts]
 Q --> PG[PostgreSQL dimensions and marts]
 O --> PG
 Q --> F[Rolling-origin forecasting]
 F --> I[Simulated policies and replenishment]
 F --> E[Versioned run exports]
 I --> E
 PG --> BI[Six-page Power BI specification]
 E --> BI
```

```mermaid
erDiagram
 common_dim_date ||--o{ m5_fact_sales_daily : date_key
 m5_dim_product ||--o{ m5_fact_sales_daily : item_id
 m5_dim_store ||--o{ m5_fact_sales_daily : store_id
 m5_dim_state ||--o{ m5_dim_store : state_id
 m5_dim_category ||--o{ m5_dim_department : category_id
 m5_dim_department ||--o{ m5_dim_product : department_id
 m5_dim_product ||--o{ m5_fact_sell_price : item_id
 m5_dim_store ||--o{ m5_fact_sell_price : store_id
 m5_dim_product ||--o{ m5_fact_forecast : item_id
 m5_dim_store ||--o{ m5_fact_forecast : store_id
 common_dim_date ||--o{ m5_fact_forecast : date_key
 m5_dim_product ||--o{ m5_fact_forecast_accuracy : item_id
 m5_dim_product ||--o{ m5_fact_inventory_policy : item_id
 m5_dim_product ||--o{ m5_fact_inventory_simulation : item_id
 common_dim_date ||--o{ m5_bridge_date_event : date_key
 m5_dim_event ||--o{ m5_bridge_date_event : event_name
 dataco_dim_order_date ||--o{ dataco_fact_delivery_performance : date_key
 dataco_dim_shipping_mode ||--o{ dataco_fact_delivery_performance : shipping_mode
 dataco_dim_market ||--o{ dataco_fact_delivery_performance : market
 dataco_dim_region ||--o{ dataco_fact_delivery_performance : region
 dataco_dim_customer_segment ||--o{ dataco_fact_delivery_performance : customer_segment
 dataco_fact_delivery_performance ||--o{ dataco_fact_orders : order_id
 dataco_dim_product_category ||--o{ dataco_fact_orders : category
 dataco_fact_orders ||--|| dataco_fact_profitability : order_item_id
```

The database uses shared calendar semantics but separate operational domains. Power BI uses independent role-playing date tables so historical source date ranges do not accidentally empty the other domain. Natural business keys are retained; no fictional cross-domain mapping is introduced. SQL table comments document grains; FKs and unique constraints enforce contracts.

The executable order is validation → Parquet → forecasting/simulation → transactional PostgreSQL load → BI. Transform and model jobs use Parquet for portability and reproducibility; the database is a serving layer and can be loaded after all outputs validate. This avoids a mandatory database dependency for the laptop demo. A PostgreSQL run uses one transaction to reload only owned tables, then builds marts and checks constraints. Point it at a dedicated project database; it replaces that database's project snapshots.

Full-mode notes: DuckDB can spill transformations to disk, global training is capped, and history is read in batches of 500 series. Full-mode forecast comparison results still require materialization; memory demand grows with series × horizon × models. Allocate sufficient RAM/disk and reduce inference batch size/training rows if needed. Simulations use an explicit pair cap and record coverage. The full M5 run has not been benchmarked on this machine.
