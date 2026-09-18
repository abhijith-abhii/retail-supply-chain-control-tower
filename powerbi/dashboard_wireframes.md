# Dashboard wireframes
Canvas: 1440 × 900. White panels on #F6F8FA, dark text, teal primary, amber uncertainty, red adverse outcomes. Minimum 11-point labels. All cards include source domain and units; currency labels remain source-specific.

## Executive Control Tower
Audience: Supply-chain VP. Scope: **M5 history | forecast | scenario panels; separate DataCo operations panel**.

```text
┌──────────────────────────────────────────────────────────────┐
│ Page title | provenance | refreshed UTC          Reset filters│ 0–64
├──────────────────────────────────────────────────────────────┤
│ Slicers and period / scenario labels                          │ 64–130
├──────────────────────────────────────────────────────────────┤
│ KPI cards, with units and definitions                         │ 130–270
├───────────────────────────────┬──────────────────────────────┤
│ Main trend / comparison       │ Risk / variance / breakdown   │ 286–540
├───────────────────────────────┼──────────────────────────────┤
│ Detail matrix / Pareto        │ Evidence and recommendations  │ 556–820
└───────────────────────────────┴──────────────────────────────┘
 Footer: actual / forecast / scenario legend and limitations     840–880
```
KPIs: Total Units Sold; Total Revenue; Forecast Units; Forecast WAPE; Inventory Value; Products at Stockout Risk; Estimated Excess Inventory; Fill Rate; Late Delivery %; Total Profit; Profit Margin %; Estimated Cost Reduction.

Visual bindings: Revenue/demand trend (date; revenue columns, units line); selected test forecast vs actual; stockout matrix (category/store, risk count); variance cards; inventory risk by category; shipping late-rate bar; recommendation text linked to executive_summary.

Slicers: M5 date, store, category; separate DataCo order-date, market; single service-level and policy.

Interactions: dimension slicers filter their own domain only. Clicking a category filters its compatible detail matrix. Suppress cross-highlighting into unrelated panels. Tooltip includes denominator, date range and provenance. Use amber/red based on configured service targets; display negative cost reduction as adverse.


## Demand Forecasting
Audience: Inventory planning manager. Scope: **Forecast dates and held-out test dates shown separately**.

```text
┌──────────────────────────────────────────────────────────────┐
│ Page title | provenance | refreshed UTC          Reset filters│ 0–64
├──────────────────────────────────────────────────────────────┤
│ Slicers and period / scenario labels                          │ 64–130
├──────────────────────────────────────────────────────────────┤
│ KPI cards, with units and definitions                         │ 130–270
├───────────────────────────────┬──────────────────────────────┤
│ Main trend / comparison       │ Risk / variance / breakdown   │ 286–540
├───────────────────────────────┼──────────────────────────────┤
│ Detail matrix / Pareto        │ Evidence and recommendations  │ 556–820
└───────────────────────────────┴──────────────────────────────┘
 Footer: actual / forecast / scenario legend and limitations     840–880
```
KPIs: Forecast Units; Forecast WAPE; Forecast Bias.

Visual bindings: Actual/forecast test lines; item-store lower/upper prediction bands; store and category accuracy bars using ratio-of-sums; comparison matrix filtered to item_store; bias by store; event/SNAP descriptive profiles. Do not sum interval bounds to claim portfolio confidence.

Slicers: Store, item, category, evaluation/forecast date. Model-comparison table is independent from selected forecast.

Interactions: dimension slicers filter their own domain only. Clicking a category filters its compatible detail matrix. Suppress cross-highlighting into unrelated panels. Tooltip includes denominator, date range and provenance. Use amber/red based on configured service targets; display negative cost reduction as adverse.


## Inventory Optimization
Audience: Inventory planning manager. Scope: **All inventory numbers labelled SIMULATED**.

```text
┌──────────────────────────────────────────────────────────────┐
│ Page title | provenance | refreshed UTC          Reset filters│ 0–64
├──────────────────────────────────────────────────────────────┤
│ Slicers and period / scenario labels                          │ 64–130
├──────────────────────────────────────────────────────────────┤
│ KPI cards, with units and definitions                         │ 130–270
├───────────────────────────────┬──────────────────────────────┤
│ Main trend / comparison       │ Risk / variance / breakdown   │ 286–540
├───────────────────────────────┼──────────────────────────────┤
│ Detail matrix / Pareto        │ Evidence and recommendations  │ 556–820
└───────────────────────────────┴──────────────────────────────┘
 Footer: actual / forecast / scenario legend and limitations     840–880
```
KPIs: Safety Stock Units; Reorder Point Units; EOQ Units; Days of Supply; Inventory Value; Estimated Cost Reduction.

Visual bindings: Item-store policy matrix; starting stockout-probability heatmap; paired baseline/optimized cost columns; ABC-XYZ matrix via product_store_performance; excess vs shortage scatter; sensitivity scenario line; fill-rate/cost trade-off scatter.

Slicers: Single-select ServiceLevel (90%,95%,98%), Policy, Scenario; product/store. Snapshot date label.

Interactions: dimension slicers filter their own domain only. Clicking a category filters its compatible detail matrix. Suppress cross-highlighting into unrelated panels. Tooltip includes denominator, date range and provenance. Use amber/red based on configured service targets; display negative cost reduction as adverse.


## Product and Store Performance
Audience: Store operations and finance. Scope: **M5 performance plus separately labelled DataCo margin inset**.

```text
┌──────────────────────────────────────────────────────────────┐
│ Page title | provenance | refreshed UTC          Reset filters│ 0–64
├──────────────────────────────────────────────────────────────┤
│ Slicers and period / scenario labels                          │ 64–130
├──────────────────────────────────────────────────────────────┤
│ KPI cards, with units and definitions                         │ 130–270
├───────────────────────────────┬──────────────────────────────┤
│ Main trend / comparison       │ Risk / variance / breakdown   │ 286–540
├───────────────────────────────┼──────────────────────────────┤
│ Detail matrix / Pareto        │ Evidence and recommendations  │ 556–820
└───────────────────────────────┴──────────────────────────────┘
 Footer: actual / forecast / scenario legend and limitations     840–880
```
KPIs: Total Revenue; Total Units Sold; Average Selling Price.

Visual bindings: Revenue-ranked store bar; category/department monthly trends; product Pareto line/columns; state revenue map or accessible bar alternative; price vs demand scatter; product-store matrix. High-sales low-margin inset uses DataCo exclusively because M5 lacks costs.

Slicers: M5 date/state/store/category/department; independent DataCo category for margin inset.

Interactions: dimension slicers filter their own domain only. Clicking a category filters its compatible detail matrix. Suppress cross-highlighting into unrelated panels. Tooltip includes denominator, date range and provenance. Use amber/red based on configured service targets; display negative cost reduction as adverse.


## Delivery and Logistics
Audience: Logistics manager. Scope: **DataCo only**.

```text
┌──────────────────────────────────────────────────────────────┐
│ Page title | provenance | refreshed UTC          Reset filters│ 0–64
├──────────────────────────────────────────────────────────────┤
│ Slicers and period / scenario labels                          │ 64–130
├──────────────────────────────────────────────────────────────┤
│ KPI cards, with units and definitions                         │ 130–270
├───────────────────────────────┬──────────────────────────────┤
│ Main trend / comparison       │ Risk / variance / breakdown   │ 286–540
├───────────────────────────────┼──────────────────────────────┤
│ Detail matrix / Pareto        │ Evidence and recommendations  │ 556–820
└───────────────────────────────┴──────────────────────────────┘
 Footer: actual / forecast / scenario legend and limitations     840–880
```
KPIs: Late Delivery %; On-Time Delivery %; Average Delay Days; Eligible Orders.

Visual bindings: Shipping-mode rates with denominators; region and market delay bars; category late rate using virtual order set; decomposition tree late orders by mode/market/region; actual vs scheduled scatter. Root-cause labels mean exploratory associations, not causal proof.

Slicers: Order date, shipping mode, region, market, customer segment. Category visuals use category-specific measures.

Interactions: dimension slicers filter their own domain only. Clicking a category filters its compatible detail matrix. Suppress cross-highlighting into unrelated panels. Tooltip includes denominator, date range and provenance. Use amber/red based on configured service targets; display negative cost reduction as adverse.


## Profitability and Root Cause
Audience: Finance manager. Scope: **DataCo only**.

```text
┌──────────────────────────────────────────────────────────────┐
│ Page title | provenance | refreshed UTC          Reset filters│ 0–64
├──────────────────────────────────────────────────────────────┤
│ Slicers and period / scenario labels                          │ 64–130
├──────────────────────────────────────────────────────────────┤
│ KPI cards, with units and definitions                         │ 130–270
├───────────────────────────────┬──────────────────────────────┤
│ Main trend / comparison       │ Risk / variance / breakdown   │ 286–540
├───────────────────────────────┼──────────────────────────────┤
│ Detail matrix / Pareto        │ Evidence and recommendations  │ 556–820
└───────────────────────────────┴──────────────────────────────┘
 Footer: actual / forecast / scenario legend and limitations     840–880
```
KPIs: Total Sales; Total Profit; Profit Margin %; Loss-Making Orders.

Visual bindings: Profit by category and market; order trend; shipping late-rate vs margin scatter using shared shipping dimension; Pareto of absolute losses on loss-making orders; decomposition tree category/market/region/segment. Keep gains and losses separate in Pareto.

Slicers: Order date, market, region, category, shipping mode; show invalid-record exclusion count.

Interactions: dimension slicers filter their own domain only. Clicking a category filters its compatible detail matrix. Suppress cross-highlighting into unrelated panels. Tooltip includes denominator, date range and provenance. Use amber/red based on configured service targets; display negative cost reduction as adverse.


## Auxiliary drill-through and tooltip pages
Create hidden `Item-store Detail` with dim_product[item_id] and dim_store[store_id] drill-through fields, last 90 days, 28-day forecast, policy and uncertainty. Create `DataCo Order Detail` with order_id, line profit and shipment attributes; no customer PII. Add Back buttons.
Create `Forecast Tooltip` with model, origin, held-out WAPE and item-level interval coverage; `Inventory Tooltip` with assumption source, service, lead time and estimated cost; `Delivery Tooltip` with eligible/late counts and delay definition. Set page type Tooltip and keep each under 360 × 260.
Create one default-state bookmark per page, selected data state enabled, and bind Reset filters to it. Dynamic title uses supplied DAX. Provide alt text and a table alternative to every map. Capture six screenshots after reconciliation in Desktop; none are represented as completed here.
