-- 1. Monthly units and revenue
SELECT date_trunc('month',date) AS month,sum(units_sold) units,sum(revenue) revenue FROM m5.fact_sales_daily GROUP BY 1 ORDER BY 1;

-- 2. Month-over-month growth
WITH m AS (SELECT date_trunc('month',date) AS month,sum(revenue) revenue FROM m5.fact_sales_daily GROUP BY 1) SELECT *,revenue/nullif(lag(revenue) OVER(ORDER BY month),0)-1 mom_growth FROM m;

-- 3. Store revenue ranking
SELECT store_id,sum(revenue) revenue,dense_rank() OVER(ORDER BY sum(revenue) DESC) rank FROM m5.fact_sales_daily GROUP BY 1;

-- 4. Category contribution
SELECT p.category_id,sum(f.revenue) revenue,sum(f.revenue)/nullif(sum(sum(f.revenue)) OVER(),0) contribution FROM m5.fact_sales_daily f JOIN m5.dim_product p USING(item_id) GROUP BY 1;

-- 5. Top products: trailing 90 days
SELECT item_id,sum(revenue) revenue FROM m5.fact_sales_daily WHERE date>(SELECT max(date)-89 FROM m5.fact_sales_daily)-1 GROUP BY 1 ORDER BY 2 DESC LIMIT 20;

-- 6. Bottom products; retain zero-demand items
SELECT item_id,sum(revenue) revenue FROM m5.fact_sales_daily GROUP BY 1 ORDER BY 2 ASC NULLS LAST LIMIT 20;

-- 7. Past-only rolling demand
SELECT item_id,store_id,date,avg(units_sold) OVER(PARTITION BY item_id,store_id ORDER BY date ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) mean7,avg(units_sold) OVER(PARTITION BY item_id,store_id ORDER BY date ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING) mean28 FROM m5.fact_sales_daily;

-- 8. Variability and zero frequency
SELECT item_id,store_id,stddev_samp(units_sold)/nullif(avg(units_sold),0) cv,avg(CASE WHEN units_sold=0 THEN 1.0 ELSE 0 END) zero_share FROM m5.fact_sales_daily GROUP BY 1,2;

-- 9. ABC, including the item that crosses a boundary
WITH r AS (SELECT item_id,sum(revenue) revenue FROM m5.fact_sales_daily GROUP BY 1),c AS(SELECT *,coalesce(sum(revenue) OVER(ORDER BY revenue DESC,item_id ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0)/nullif(sum(revenue) OVER(),0) prior_share FROM r) SELECT *,CASE WHEN prior_share<.8 THEN 'A' WHEN prior_share<.95 THEN 'B' ELSE 'C' END abc FROM c;

-- 10. XYZ, CV thresholds are configurable planning heuristics
SELECT item_id,store_id,CASE WHEN avg(CASE WHEN units_sold=0 THEN 1.0 ELSE 0 END)>=.5 THEN 'Z' WHEN stddev_samp(units_sold)/nullif(avg(units_sold),0)<=.5 THEN 'X' WHEN stddev_samp(units_sold)/nullif(avg(units_sold),0)<=1 THEN 'Y' ELSE 'Z' END xyz FROM m5.fact_sales_daily GROUP BY 1,2;

-- 11. Combined ABC-XYZ at item-store grain
WITH r AS(SELECT item_id,store_id,sum(revenue) revenue,stddev_samp(units_sold)/nullif(avg(units_sold),0) cv,avg(CASE WHEN units_sold=0 THEN 1.0 ELSE 0 END) zero_share FROM m5.fact_sales_daily GROUP BY 1,2), c AS(SELECT *,coalesce(sum(revenue) OVER(ORDER BY revenue DESC,item_id,store_id ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0)/nullif(sum(revenue) OVER(),0) prior_share FROM r) SELECT *,concat(CASE WHEN prior_share<.8 THEN 'A' WHEN prior_share<.95 THEN 'B' ELSE 'C' END,'-',CASE WHEN zero_share>=.5 THEN 'Z' WHEN cv<=.5 THEN 'X' WHEN cv<=1 THEN 'Y' ELSE 'Z' END) abc_xyz FROM c;

-- 12. Price versus demand changes: descriptive, not causal
SELECT item_id,store_id,date,sell_price/nullif(lag(sell_price) OVER w,0)-1 price_change,units_sold-lag(units_sold) OVER w demand_change,lead(units_sold) OVER w next_day_units FROM m5.fact_sales_daily WINDOW w AS(PARTITION BY item_id,store_id ORDER BY date);

-- 13. Event association, unadjusted for seasonal confounding
SELECT item_id,avg(units_sold) FILTER(WHERE event_flag=1)/nullif(avg(units_sold) FILTER(WHERE event_flag=0),0)-1 unadjusted_event_uplift FROM m5.fact_sales_daily GROUP BY 1;

-- 14. Forecast WAPE by store; locked test only
SELECT store_id,model,sum(absolute_error)/nullif(sum(actual_units),0) wape FROM m5.fact_forecast_accuracy WHERE split_role='test' GROUP BY 1,2;

-- 15. Forecast WAPE by category
SELECT p.category_id,f.model,sum(f.absolute_error)/nullif(sum(f.actual_units),0) wape FROM m5.fact_forecast_accuracy f JOIN m5.dim_product p USING(item_id) WHERE split_role='test' GROUP BY 1,2;

-- 16. Highest modeled stockout risk; select one scenario
SELECT * FROM m5.fact_inventory_policy WHERE target_service_level=.95 ORDER BY stockout_probability DESC LIMIT 20;

-- 17. Excess simulated inventory
SELECT item_id,store_id,excess_units,excess_value FROM m5.fact_inventory_policy WHERE target_service_level=.95 AND excess_units>0 ORDER BY excess_value DESC;

-- 18. Simulated inventory investment by category
SELECT p.category_id,sum(i.inventory_value) value FROM m5.fact_inventory_policy i JOIN m5.dim_product p USING(item_id) WHERE target_service_level=.95 GROUP BY 1;

-- 19. Late rate by shipping mode, one row per order
SELECT shipping_mode,count(*) eligible_orders,avg(late_order::numeric) late_rate FROM dataco.fact_delivery_performance WHERE delivery_eligible GROUP BY 1;

-- 20. Delay by region, including on-time zero delay
SELECT region,avg(positive_delay_days) average_delay,percentile_cont(.9) WITHIN GROUP(ORDER BY positive_delay_days) p90_delay FROM dataco.fact_delivery_performance WHERE delivery_eligible GROUP BY 1;

-- 21. Profit margin by category, ratio of sums
SELECT category,sum(profit)/nullif(sum(sales),0) margin FROM dataco.fact_orders WHERE NOT invalid_sales_flag GROUP BY 1;

-- 22. Loss-making orders after summing lines
SELECT order_id,sum(sales) sales,sum(profit) profit FROM dataco.fact_orders WHERE NOT invalid_sales_flag GROUP BY 1 HAVING sum(profit)<0 ORDER BY 3;

-- 23. High-sales low-profit products: data-driven sales threshold
WITH p AS(SELECT product_name,sum(sales) sales,sum(profit) profit FROM dataco.fact_orders WHERE NOT invalid_sales_flag GROUP BY 1) SELECT *,profit/nullif(sales,0) margin FROM p WHERE sales>=(SELECT percentile_cont(.75) WITHIN GROUP(ORDER BY sales) FROM p) AND profit/nullif(sales,0)<.05;

-- 24. Pareto of late orders by region
WITH r AS(SELECT region,sum(late_order) late_orders FROM dataco.fact_delivery_performance WHERE delivery_eligible GROUP BY 1) SELECT *,sum(late_orders) OVER(ORDER BY late_orders DESC,region)/nullif(sum(late_orders) OVER(),0)::numeric cumulative_share FROM r;

-- 25. Executive domains remain separate
SELECT * FROM mart.mart_executive_kpis;

-- 26. Recursive CTE creates a 28-day planning calendar
WITH RECURSIVE dates AS(SELECT max(date)+1 AS date,1 AS horizon FROM m5.fact_sales_daily UNION ALL SELECT date+1,horizon+1 FROM dates WHERE horizon<28) SELECT * FROM dates;

-- 27. Query optimization: inspect actual I/O, not only estimated cost
EXPLAIN (ANALYZE,BUFFERS) SELECT store_id,sum(revenue) FROM m5.fact_sales_daily WHERE date_key BETWEEN 20160101 AND 20160131 GROUP BY store_id;

-- 28. Scenario comparison: aggregate each run before averaging
WITH k AS(SELECT policy,run_id,sum(total_inventory_cost) cost FROM m5.fact_inventory_simulation WHERE target_service_level=.95 AND scenario='base' GROUP BY 1,2), p AS(SELECT run_id,max(cost) FILTER(WHERE policy='baseline') baseline,max(cost) FILTER(WHERE policy='optimized') optimized FROM k GROUP BY 1) SELECT avg(baseline-optimized) estimated_cost_reduction,stddev_samp(baseline-optimized) between_run_std FROM p;
