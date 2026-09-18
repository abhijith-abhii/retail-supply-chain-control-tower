# Output field dictionary
Generated from the executed Parquet schemas. Currency units are source-specific; never add M5 and DataCo money.
Null means unavailable or undefined, never automatically zero. Each forecast has one origin/model; every simulation row includes policy, service, scenario and run.

## abc_xyz_segmentation
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| store_id | string | observed | M5 store natural key. |
| abc | string | derived | Revenue concentration class using prior cumulative share: A <80%, B <95%, C remainder. |
| xyz | string | derived | Variability class based on configured CV thresholds; high zero frequency forces Z. |
| abc_xyz | string | derived | Concatenated ABC and XYZ planning segment, e.g. A-X. |
| volume_segment | string | derived | Low/medium/high thirds of training mean-demand percentile rank. |
| coefficient_of_variation | double | derived | Sample demand standard deviation / mean; null for zero mean. |
| cumulative_revenue_share | double | derived | Running revenue contribution in descending revenue order, including current pair. |

## bridge_date_event
| Field | Type | Provenance | Definition |
|---|---|---|---|
| date_key | int32 | derived | Integer YYYYMMDD key derived from calendar date. |
| event_name | string | observed | First source calendar event name; nullable. |

## dataco_category_delivery
| Field | Type | Provenance | Definition |
|---|---|---|---|
| category | string | observed | Normalized DataCo product category; independent of M5 categories. |
| orders | int64 | derived | Distinct order count at the output aggregation grain. |
| eligible_orders | int64 | derived | Count of distinct eligible orders, or distinct order-category pairs in category output. |
| late_orders | int64 | derived | Number of eligible late orders in a segment. |
| late_delivery_rate | double | derived | Late eligible orders / eligible orders, fraction 0–1; null for empty denominator. |

## dataco_delivery_performance
| Field | Type | Provenance | Definition |
|---|---|---|---|
| order_id | int64 | observed | DataCo business order key; repeated across order lines, not a customer identity. |
| order_date | timestamp[ns] | observed | Parsed DataCo order calendar date; time of day discarded. |
| shipping_mode | string | observed | Normalized DataCo shipping service name. |
| market | string | observed | Normalized DataCo market; independent of M5 geography. |
| region | string | observed | Normalized DataCo order region. |
| customer_segment | string | observed | Normalized business customer segment; no personal identity. |
| actual_shipping_days | int64 | observed | Source reported actual shipping duration in days; not last-mile scan evidence. |
| scheduled_shipping_days | int64 | observed | Source promised shipping duration in days. |
| delivery_eligible | bool | derived | True for valid 0–configured-max shipping durations excluding cancelled/suspected-fraud orders. |
| late_order | int64 | derived | 1 when actual shipping exceeds scheduled, 0 when on time, null if ineligible. |
| delay_days | int64 | derived | Signed actual minus scheduled shipping days on eligible orders. |
| positive_delay_days | int64 | derived | Maximum of signed delay and zero; null if ineligible. |
| date_key | int64 | derived | Integer YYYYMMDD key derived from calendar date. |

## dataco_monthly
| Field | Type | Provenance | Definition |
|---|---|---|---|
| period | timestamp[ns] | derived | Start date of the displayed daily, weekly or monthly aggregate. |
| sales | double | observed | Configured DataCo line net-sales amount; defaults to order_item_total. |
| profit | double | observed | Configured DataCo line benefit amount; defaults to benefit_per_order; not repeated alias sum. |
| orders | int64 | derived | Distinct order count at the output aggregation grain. |

## dataco_order_profit
| Field | Type | Provenance | Definition |
|---|---|---|---|
| order_id | int64 | observed | DataCo business order key; repeated across order lines, not a customer identity. |
| sales | double | observed | Configured DataCo line net-sales amount; defaults to order_item_total. |
| profit | double | observed | Configured DataCo line benefit amount; defaults to benefit_per_order; not repeated alias sum. |
| loss_making_order | bool | derived | True if sum of valid line profit for a DataCo order is negative. |

## dataco_profitability
| Field | Type | Provenance | Definition |
|---|---|---|---|
| order_item_id | int64 | observed | Unique DataCo business order-line key. |
| order_id | int64 | observed | DataCo business order key; repeated across order lines, not a customer identity. |
| order_date | timestamp[ns] | observed | Parsed DataCo order calendar date; time of day discarded. |
| date_key | int64 | derived | Integer YYYYMMDD key derived from calendar date. |
| shipping_mode | string | observed | Normalized DataCo shipping service name. |
| market | string | observed | Normalized DataCo market; independent of M5 geography. |
| region | string | observed | Normalized DataCo order region. |
| category | string | observed | Normalized DataCo product category; independent of M5 categories. |
| customer_segment | string | observed | Normalized business customer segment; no personal identity. |
| product_name | string | observed | Normalized DataCo product label. |
| quantity | int64 | observed | Source DataCo order-line quantity. |
| sales | double | observed | Configured DataCo line net-sales amount; defaults to order_item_total. |
| profit | double | observed | Configured DataCo line benefit amount; defaults to benefit_per_order; not repeated alias sum. |
| invalid_sales_flag | bool | derived | Negative configured sales or negative quantity; excluded from headline profit measures. |
| abnormal_profit_flag | bool | derived | Absolute line profit greater than twice absolute line sales; flag only, not automatic deletion. |
| profit_margin | double | derived | Aggregate or line profit / matching sales, depending on table grain; undefined at zero sales. |
| loss_making_line | bool | derived | True if a DataCo line has negative configured profit. |

## dataco_profitability_summary
| Field | Type | Provenance | Definition |
|---|---|---|---|
| segment | string | derived | Value of the corresponding segment or summary dimension. |
| sales | double | observed | Configured DataCo line net-sales amount; defaults to order_item_total. |
| profit | double | observed | Configured DataCo line benefit amount; defaults to benefit_per_order; not repeated alias sum. |
| order_count | int64 | derived | Distinct order count in a profitability group; non-additive across categories. |
| dimension | string | derived | Column whose values define a grouped operational output. |
| profit_margin | double | derived | Aggregate or line profit / matching sales, depending on table grain; undefined at zero sales. |

## dataco_shipping_mode_performance
| Field | Type | Provenance | Definition |
|---|---|---|---|
| dimension | string | derived | Column whose values define a grouped operational output. |
| segment | string | derived | Value of the corresponding segment or summary dimension. |
| total_orders | int64 | derived | Number of orders including ineligible outcomes within a segment. |
| eligible_orders | int64 | derived | Count of distinct eligible orders, or distinct order-category pairs in category output. |
| late_orders | int64 | derived | Number of eligible late orders in a segment. |
| late_delivery_rate | double | derived | Late eligible orders / eligible orders, fraction 0–1; null for empty denominator. |
| average_delay_days | double | derived | Mean positive delay across eligible orders, including zero for on-time orders. |
| average_signed_delay | double | derived | Mean actual minus scheduled duration across eligible orders; can be negative. |
| actual_shipping_days | double | observed | Source reported actual shipping duration in days; not last-mile scan evidence. |
| scheduled_shipping_days | double | observed | Source promised shipping duration in days. |

## demand_forecasts_28d
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| store_id | string | observed | M5 store natural key. |
| state_id | string | observed | M5 state code CA, TX or WI. |
| category_id | string | observed | M5 category natural key. |
| department_id | string | observed | M5 department natural key. |
| origin | timestamp[ns] | derived | Last historical date available to the forecast. |
| date | timestamp[ns] | observed | Calendar date represented by the observation or prediction. |
| date_key | int64 | derived | Integer YYYYMMDD key derived from calendar date. |
| horizon | int64 | derived | Integer number of days after origin. |
| model | string | derived | Forecast or classifier name; different forecast levels must not be pooled. |
| forecast_units | double | forecast | Nonnegative model prediction in units for one item-store-date-origin-model. |
| scale | double | derived | Mean squared training first difference after first nonzero sale; undefined for constants. |
| lower_80 | double | forecast | Lower empirical residual bound for nominal 80% interval, clipped at zero and below point. |
| upper_80 | double | forecast | Upper empirical residual bound for nominal 80% interval, at least point forecast. |
| lower_95 | double | forecast | Lower empirical residual bound for nominal 95% interval; not additive into portfolio coverage. |
| upper_95 | double | forecast | Upper empirical residual bound for nominal 95% interval; not additive into portfolio coverage. |

## dim_category
| Field | Type | Provenance | Definition |
|---|---|---|---|
| category_id | string | observed | M5 category natural key. |

## dim_customer_segment
| Field | Type | Provenance | Definition |
|---|---|---|---|
| customer_segment | string | observed | Normalized business customer segment; no personal identity. |

## dim_date
| Field | Type | Provenance | Definition |
|---|---|---|---|
| date | timestamp[ns] | observed | Calendar date represented by the observation or prediction. |
| date_key | int64 | derived | Integer YYYYMMDD key derived from calendar date. |
| year | int32 | derived | Calendar year. |
| month | int32 | derived | Calendar month 1–12. |
| quarter | int32 | derived | Calendar quarter 1–4. |

## dim_department
| Field | Type | Provenance | Definition |
|---|---|---|---|
| department_id | string | observed | M5 department natural key. |
| category_id | string | observed | M5 category natural key. |

## dim_event
| Field | Type | Provenance | Definition |
|---|---|---|---|
| event_name | string | observed | First source calendar event name; nullable. |
| event_type | string | observed | First source calendar event type; nullable. |

## dim_market
| Field | Type | Provenance | Definition |
|---|---|---|---|
| market | string | observed | Normalized DataCo market; independent of M5 geography. |

## dim_order_date
| Field | Type | Provenance | Definition |
|---|---|---|---|
| date | timestamp[ns] | observed | Calendar date represented by the observation or prediction. |
| date_key | int64 | derived | Integer YYYYMMDD key derived from calendar date. |
| year | int32 | derived | Calendar year. |
| month | int32 | derived | Calendar month 1–12. |
| quarter | int32 | derived | Calendar quarter 1–4. |

## dim_product
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| department_id | string | observed | M5 department natural key. |
| category_id | string | observed | M5 category natural key. |

## dim_product_category
| Field | Type | Provenance | Definition |
|---|---|---|---|
| category | string | observed | Normalized DataCo product category; independent of M5 categories. |

## dim_region
| Field | Type | Provenance | Definition |
|---|---|---|---|
| region | string | observed | Normalized DataCo order region. |

## dim_shipping_mode
| Field | Type | Provenance | Definition |
|---|---|---|---|
| shipping_mode | string | observed | Normalized DataCo shipping service name. |

## dim_state
| Field | Type | Provenance | Definition |
|---|---|---|---|
| state_id | string | observed | M5 state code CA, TX or WI. |

## dim_store
| Field | Type | Provenance | Definition |
|---|---|---|---|
| store_id | string | observed | M5 store natural key. |
| state_id | string | observed | M5 state code CA, TX or WI. |

## excess_inventory
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| store_id | string | observed | M5 store natural key. |
| category_id | string | observed | M5 category natural key. |
| department_id | string | observed | M5 department natural key. |
| state_id | string | observed | M5 state code CA, TX or WI. |
| average_daily_demand | double | derived | Trailing 90-day pre-origin recorded-sales mean for an item-store. |
| demand_std | double | derived | Sample standard deviation of trailing 90-day recorded sales. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| zero_demand_share | double | derived | Fraction of trailing item-store days with zero recorded sales. |
| last_price | double | derived | Most recent non-null price known at the summary or forecast origin. |
| supplier_id | string | simulated | SIM_ plus M5 category; illustrative supplier group, never real Walmart supplier. |
| average_lead_time_days | int64 | simulated | Assumed expected replenishment lead time in days. |
| lead_time_standard_deviation | double | simulated | Assumed lead-time standard deviation in days. |
| ordering_cost_per_order | double | simulated | Assumed fixed currency cost each time a purchase order is placed. |
| annual_holding_cost_rate | double | simulated | Annual holding cost as fraction of assumed unit cost. |
| estimated_unit_cost | double | simulated | Assumed cost-to-price ratio times last known price, with positive floor. |
| target_service_level | double | simulated | Scenario cycle-service target in (0,1); does not equal fill rate. |
| initial_inventory | int64 | simulated | Assumed opening on-hand units before first simulation demand. |
| review_period_days | int64 | simulated | Number of calendar days between ordering reviews. |
| lost_sale_penalty | double | simulated | Assumed cost per unfulfilled unit; not guaranteed lost revenue. |
| minimum_order_quantity | int64 | simulated | Smallest nonzero purchase quantity before pack rounding. |
| case_pack_size | int64 | simulated | Order quantities must be integer multiples of this positive unit count. |
| assumption_type | string | simulated | Explicit simulated_not_walmart provenance label. |
| seed | int64 | simulated | Fixed pseudo-random seed for reproducible assumption generation. |
| forecast_daily_demand | double | forecast | Mean predicted daily units over the planning horizon. |
| forecast_error_std | double | derived | Sample standard deviation of pre-test selected-model forecast residuals per item-store. |
| as_of_date | timestamp[ns] | derived | Snapshot date at which an inventory recommendation was generated. |
| safety_stock | double | simulated | Normal-approximation lead-time buffer units based on assumed service level. |
| expected_lead_time_demand | double | simulated | Forecast daily mean multiplied by mean lead days. |
| reorder_point | double | simulated | Expected lead-time demand plus lead-time safety stock; continuous-review reference. |
| protection_safety_stock | double | simulated | Safety units covering lead time plus periodic review interval. |
| order_up_to_level | double | simulated | Forecast mean times lead-plus-review days plus protection safety stock. |
| eoq | double | simulated | Square root of 2 × annualized units × fixed ordering cost / annual per-unit holding cost. |
| days_of_supply | double | simulated | Assumed initial inventory / forecast daily mean; undefined for zero mean. |
| inventory_value | double | simulated | Assumed initial stock multiplied by estimated unit cost. |
| demand_uncertainty_std | double | simulated | Forecast-error SD used for inventory policy, falling back to raw demand SD if unavailable. |
| stockout_probability | double | simulated | Normal lead-time demand tail above initial stock assuming no initial incoming POs. |
| recommended_order_quantity | int64 | simulated | Larger of EOQ or target shortage, rounded to MOQ/case pack, zero if no shortage. |
| excess_units | double | simulated | Positive initial inventory above protection order-up-to target. |
| excess_value | double | simulated | Excess units multiplied by estimated unit cost. |

## executive_kpis
| Field | Type | Provenance | Definition |
|---|---|---|---|
| domain | string | derived | M5 or DataCo; domains must never be combined as one retailer. |
| metric_type | string | derived | Historical, forecast or scenario_estimate provenance class for executive values. |
| metric | string | derived | Executive KPI identifier. |
| value | double | derived | Numeric executive KPI value; meaning and unit depend on metric and domain. |
| data_provenance | string | derived | synthetic_fixture or kaggle; never substitute one for the other. |

## fact_sell_price
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| store_id | string | observed | M5 store natural key. |
| wm_yr_wk | int64 | observed | M5 retail calendar week identifier. |
| sell_price | double | observed | M5 listed weekly item-store selling price, source currency per unit. |

## forecast_accuracy_by_segment
| Field | Type | Provenance | Definition |
|---|---|---|---|
| segment_type | string | derived | Dimension over which forecast accuracy is summarized. |
| segment | string | derived | Value of the corresponding segment or summary dimension. |
| model | string | derived | Forecast or classifier name; different forecast levels must not be pooled. |
| mae | double | derived | Mean absolute forecast error in units. |
| rmse | double | derived | Square root of mean squared forecast error in units. |
| wape | double | derived | Sum absolute forecast error / sum actual units; null when denominator is zero. |
| mape | double | derived | Mean absolute percentage error over nonzero actuals only; null if none. |
| bias | double | derived | Sum(forecast-actual) / sum(actual); null for zero total actuals. |
| rmsse | double | derived | Square root of pooled row squared-error / training-series scale, valid positive scales only; not WRMSSE. |

## forecast_backtest_all
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| store_id | string | observed | M5 store natural key. |
| state_id | string | observed | M5 state code CA, TX or WI. |
| category_id | string | observed | M5 category natural key. |
| department_id | string | observed | M5 department natural key. |
| origin | timestamp[ns] | derived | Last historical date available to the forecast. |
| date | timestamp[ns] | observed | Calendar date represented by the observation or prediction. |
| date_key | int64 | derived | Integer YYYYMMDD key derived from calendar date. |
| horizon | int64 | derived | Integer number of days after origin. |
| model | string | derived | Forecast or classifier name; different forecast levels must not be pooled. |
| forecast_units | double | forecast | Nonnegative model prediction in units for one item-store-date-origin-model. |
| scale | double | derived | Mean squared training first difference after first nonzero sale; undefined for constants. |
| actual_units | int64 | observed | Observed held-out M5 sales units matched to a forecast. |
| fold | int64 | derived | Chronological rolling-origin fold index. |
| split_role | string | derived | Calibration, selection or locked test role. |
| error | double | derived | Forecast units minus actual units; positive means overprediction. |
| absolute_error | double | derived | Absolute value of row prediction error. |

## forecast_backtest_selected
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| store_id | string | observed | M5 store natural key. |
| state_id | string | observed | M5 state code CA, TX or WI. |
| category_id | string | observed | M5 category natural key. |
| department_id | string | observed | M5 department natural key. |
| origin | timestamp[ns] | derived | Last historical date available to the forecast. |
| date | timestamp[ns] | observed | Calendar date represented by the observation or prediction. |
| date_key | int64 | derived | Integer YYYYMMDD key derived from calendar date. |
| horizon | int64 | derived | Integer number of days after origin. |
| model | string | derived | Forecast or classifier name; different forecast levels must not be pooled. |
| forecast_units | double | forecast | Nonnegative model prediction in units for one item-store-date-origin-model. |
| scale | double | derived | Mean squared training first difference after first nonzero sale; undefined for constants. |
| actual_units | int64 | observed | Observed held-out M5 sales units matched to a forecast. |
| fold | int64 | derived | Chronological rolling-origin fold index. |
| split_role | string | derived | Calibration, selection or locked test role. |
| error | double | derived | Forecast units minus actual units; positive means overprediction. |
| absolute_error | double | derived | Absolute value of row prediction error. |
| lower_80 | double | forecast | Lower empirical residual bound for nominal 80% interval, clipped at zero and below point. |
| upper_80 | double | forecast | Upper empirical residual bound for nominal 80% interval, at least point forecast. |
| lower_95 | double | forecast | Lower empirical residual bound for nominal 95% interval; not additive into portfolio coverage. |
| upper_95 | double | forecast | Upper empirical residual bound for nominal 95% interval; not additive into portfolio coverage. |
| covered_80 | bool | derived | Whether held-out actual is inside the nominal 80% interval. |
| covered_95 | bool | derived | Whether held-out actual is inside the nominal 95% interval. |

## forecast_model_metrics
| Field | Type | Provenance | Definition |
|---|---|---|---|
| model | string | derived | Forecast or classifier name; different forecast levels must not be pooled. |
| fold | int64 | derived | Chronological rolling-origin fold index. |
| split_role | string | derived | Calibration, selection or locked test role. |
| origin | timestamp[ns] | derived | Last historical date available to the forecast. |
| validation_start | timestamp[ns] | derived | First held-out date in the fold. |
| validation_end | timestamp[ns] | derived | Last held-out date in the fold. |
| forecast_level | string | derived | item_store or selected_portfolio_total; aggregate models are separate diagnostics. |
| training_seconds | double | derived | Measured model-fit time in seconds; baseline fit is zero. |
| mae | double | derived | Mean absolute forecast error in units. |
| rmse | double | derived | Square root of mean squared forecast error in units. |
| wape | double | derived | Sum absolute forecast error / sum actual units; null when denominator is zero. |
| mape | double | derived | Mean absolute percentage error over nonzero actuals only; null if none. |
| bias | double | derived | Sum(forecast-actual) / sum(actual); null for zero total actuals. |
| rmsse | double | derived | Square root of pooled row squared-error / training-series scale, valid positive scales only; not WRMSSE. |

## inventory_assumptions
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| store_id | string | observed | M5 store natural key. |
| supplier_id | string | simulated | SIM_ plus M5 category; illustrative supplier group, never real Walmart supplier. |
| average_lead_time_days | int64 | simulated | Assumed expected replenishment lead time in days. |
| lead_time_standard_deviation | double | simulated | Assumed lead-time standard deviation in days. |
| ordering_cost_per_order | double | simulated | Assumed fixed currency cost each time a purchase order is placed. |
| annual_holding_cost_rate | double | simulated | Annual holding cost as fraction of assumed unit cost. |
| estimated_unit_cost | double | simulated | Assumed cost-to-price ratio times last known price, with positive floor. |
| target_service_level | double | simulated | Scenario cycle-service target in (0,1); does not equal fill rate. |
| initial_inventory | int64 | simulated | Assumed opening on-hand units before first simulation demand. |
| review_period_days | int64 | simulated | Number of calendar days between ordering reviews. |
| lost_sale_penalty | double | simulated | Assumed cost per unfulfilled unit; not guaranteed lost revenue. |
| minimum_order_quantity | int64 | simulated | Smallest nonzero purchase quantity before pack rounding. |
| case_pack_size | int64 | simulated | Order quantities must be integer multiples of this positive unit count. |
| assumption_type | string | simulated | Explicit simulated_not_walmart provenance label. |
| seed | int64 | simulated | Fixed pseudo-random seed for reproducible assumption generation. |

## inventory_policy_recommendations
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| store_id | string | observed | M5 store natural key. |
| category_id | string | observed | M5 category natural key. |
| department_id | string | observed | M5 department natural key. |
| state_id | string | observed | M5 state code CA, TX or WI. |
| average_daily_demand | double | derived | Trailing 90-day pre-origin recorded-sales mean for an item-store. |
| demand_std | double | derived | Sample standard deviation of trailing 90-day recorded sales. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| zero_demand_share | double | derived | Fraction of trailing item-store days with zero recorded sales. |
| last_price | double | derived | Most recent non-null price known at the summary or forecast origin. |
| supplier_id | string | simulated | SIM_ plus M5 category; illustrative supplier group, never real Walmart supplier. |
| average_lead_time_days | int64 | simulated | Assumed expected replenishment lead time in days. |
| lead_time_standard_deviation | double | simulated | Assumed lead-time standard deviation in days. |
| ordering_cost_per_order | double | simulated | Assumed fixed currency cost each time a purchase order is placed. |
| annual_holding_cost_rate | double | simulated | Annual holding cost as fraction of assumed unit cost. |
| estimated_unit_cost | double | simulated | Assumed cost-to-price ratio times last known price, with positive floor. |
| target_service_level | double | simulated | Scenario cycle-service target in (0,1); does not equal fill rate. |
| initial_inventory | int64 | simulated | Assumed opening on-hand units before first simulation demand. |
| review_period_days | int64 | simulated | Number of calendar days between ordering reviews. |
| lost_sale_penalty | double | simulated | Assumed cost per unfulfilled unit; not guaranteed lost revenue. |
| minimum_order_quantity | int64 | simulated | Smallest nonzero purchase quantity before pack rounding. |
| case_pack_size | int64 | simulated | Order quantities must be integer multiples of this positive unit count. |
| assumption_type | string | simulated | Explicit simulated_not_walmart provenance label. |
| seed | int64 | simulated | Fixed pseudo-random seed for reproducible assumption generation. |
| forecast_daily_demand | double | forecast | Mean predicted daily units over the planning horizon. |
| forecast_error_std | double | derived | Sample standard deviation of pre-test selected-model forecast residuals per item-store. |
| as_of_date | timestamp[ns] | derived | Snapshot date at which an inventory recommendation was generated. |
| safety_stock | double | simulated | Normal-approximation lead-time buffer units based on assumed service level. |
| expected_lead_time_demand | double | simulated | Forecast daily mean multiplied by mean lead days. |
| reorder_point | double | simulated | Expected lead-time demand plus lead-time safety stock; continuous-review reference. |
| protection_safety_stock | double | simulated | Safety units covering lead time plus periodic review interval. |
| order_up_to_level | double | simulated | Forecast mean times lead-plus-review days plus protection safety stock. |
| eoq | double | simulated | Square root of 2 × annualized units × fixed ordering cost / annual per-unit holding cost. |
| days_of_supply | double | simulated | Assumed initial inventory / forecast daily mean; undefined for zero mean. |
| inventory_value | double | simulated | Assumed initial stock multiplied by estimated unit cost. |
| demand_uncertainty_std | double | simulated | Forecast-error SD used for inventory policy, falling back to raw demand SD if unavailable. |
| stockout_probability | double | simulated | Normal lead-time demand tail above initial stock assuming no initial incoming POs. |
| recommended_order_quantity | int64 | simulated | Larger of EOQ or target shortage, rounded to MOQ/case pack, zero if no shortage. |
| excess_units | double | simulated | Positive initial inventory above protection order-up-to target. |
| excess_value | double | simulated | Excess units multiplied by estimated unit cost. |

## inventory_sensitivity
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| store_id | string | observed | M5 store natural key. |
| policy | string | simulated | baseline or optimized replenishment policy. |
| scenario | string | simulated | Base or named one-factor-at-a-time sensitivity case. |
| target_service_level | double | simulated | Scenario cycle-service target in (0,1); does not equal fill rate. |
| run_id | int64 | simulated | Monte Carlo repeat index; average repeated worlds rather than summing. |
| actual_demand | double | observed | Recorded held-out sales used as simulation demand proxy, not uncensored demand. |
| fulfilled_units | double | simulated | Minimum of available inventory and observed demand proxy. |
| lost_sales_units | double | simulated | Demand proxy minus fulfilled units; no backorders carried. |
| lost_sales_value | double | simulated | Lost units valued at origin-time selling price; hypothetical revenue loss. |
| average_inventory | double | simulated | Mean end-of-day units over the replay horizon for one item-store-policy-scenario-run. |
| maximum_inventory | double | simulated | Maximum closing units during replay. |
| stockout_days | int64 | simulated | Sum of item-store-days with lost demand. |
| holding_cost | double | simulated | Closing units × unit cost × annual holding rate / 365. |
| ordering_cost | double | simulated | Fixed assumed order cost if a positive order was placed, otherwise zero. |
| lost_sale_cost | double | simulated | Lost units multiplied by assumed lost-sale penalty. |
| total_inventory_cost | double | simulated | Holding + ordering + lost-sale cost; excludes purchase spend and terminal valuation. |
| completed_cycles | int64 | simulated | Completed receipt-to-receipt replenishment cycles; first and unfinished cycles excluded. |
| successful_cycles | int64 | simulated | Completed cycles with no lost demand between consecutive receipts. |
| days | int64 | simulated | Number of replay dates for the KPI row. |
| fill_rate | double | simulated | Fulfilled units / demand proxy; null for zero demand. |
| cycle_service_level | double | simulated | Successful completed cycles / completed cycles; null if none completed. |
| inventory_turnover | double | simulated | Annualized fulfilled units / average inventory; unit proxy, not financial COGS turnover. |
| baseline_cost | double | simulated | Paired baseline total cost at the same item-store-service-scenario-run. |
| baseline_lost_sales_value | double | simulated | Paired baseline unfulfilled units valued at origin price. |
| estimated_cost_reduction | double | simulated | Baseline cost minus current policy cost; negative means worse scenario cost. |
| estimated_revenue_protected | double | simulated | Baseline lost-sales value minus current policy lost-sales value; scenario only. |
| sensitivity_factor | string | simulated | Assumption varied in the one-factor sensitivity case, or none for base. |
| multiplier | double | simulated | 0.5, 1, or 1.5 factor applied to the named assumption. |

## inventory_simulation_daily
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| store_id | string | observed | M5 store natural key. |
| date | timestamp[ns] | observed | Calendar date represented by the observation or prediction. |
| policy | string | simulated | baseline or optimized replenishment policy. |
| scenario | string | simulated | Base or named one-factor-at-a-time sensitivity case. |
| run_id | int64 | simulated | Monte Carlo repeat index; average repeated worlds rather than summing. |
| target_service_level | double | simulated | Scenario cycle-service target in (0,1); does not equal fill rate. |
| opening_inventory | double | simulated | On-hand units before today's receipts and demand. |
| arrivals | int64 | simulated | Units received today from previously placed purchase orders. |
| forecast_demand | double | forecast | Daily origin-time forecast passed into inventory replay. |
| actual_demand | double | observed | Recorded held-out sales used as simulation demand proxy, not uncensored demand. |
| fulfilled_units | double | simulated | Minimum of available inventory and observed demand proxy. |
| lost_sales_units | double | simulated | Demand proxy minus fulfilled units; no backorders carried. |
| order_quantity | int64 | simulated | Units ordered after today's demand at a review opportunity. |
| in_transit_units | int64 | simulated | All placed units still awaiting arrival at end of day, including new orders. |
| closing_inventory | double | simulated | Opening units plus receipts minus fulfillment; nonnegative. |
| stockout_event | int64 | simulated | 1 when any demand is lost on the item-store-day. |
| holding_cost | double | simulated | Closing units × unit cost × annual holding rate / 365. |
| ordering_cost | double | simulated | Fixed assumed order cost if a positive order was placed, otherwise zero. |
| lost_sale_cost | double | simulated | Lost units multiplied by assumed lost-sale penalty. |
| total_inventory_cost | double | simulated | Holding + ordering + lost-sale cost; excludes purchase spend and terminal valuation. |
| lost_sales_value | double | simulated | Lost units valued at origin-time selling price; hypothetical revenue loss. |
| estimated_unit_cost | double | simulated | Assumed cost-to-price ratio times last known price, with positive floor. |
| completed_cycles | int64 | simulated | Completed receipt-to-receipt replenishment cycles; first and unfinished cycles excluded. |
| successful_cycles | int64 | simulated | Completed cycles with no lost demand between consecutive receipts. |

## inventory_simulation_kpis
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| store_id | string | observed | M5 store natural key. |
| policy | string | simulated | baseline or optimized replenishment policy. |
| scenario | string | simulated | Base or named one-factor-at-a-time sensitivity case. |
| target_service_level | double | simulated | Scenario cycle-service target in (0,1); does not equal fill rate. |
| run_id | int64 | simulated | Monte Carlo repeat index; average repeated worlds rather than summing. |
| actual_demand | double | observed | Recorded held-out sales used as simulation demand proxy, not uncensored demand. |
| fulfilled_units | double | simulated | Minimum of available inventory and observed demand proxy. |
| lost_sales_units | double | simulated | Demand proxy minus fulfilled units; no backorders carried. |
| lost_sales_value | double | simulated | Lost units valued at origin-time selling price; hypothetical revenue loss. |
| average_inventory | double | simulated | Mean end-of-day units over the replay horizon for one item-store-policy-scenario-run. |
| maximum_inventory | double | simulated | Maximum closing units during replay. |
| stockout_days | int64 | simulated | Sum of item-store-days with lost demand. |
| holding_cost | double | simulated | Closing units × unit cost × annual holding rate / 365. |
| ordering_cost | double | simulated | Fixed assumed order cost if a positive order was placed, otherwise zero. |
| lost_sale_cost | double | simulated | Lost units multiplied by assumed lost-sale penalty. |
| total_inventory_cost | double | simulated | Holding + ordering + lost-sale cost; excludes purchase spend and terminal valuation. |
| completed_cycles | int64 | simulated | Completed receipt-to-receipt replenishment cycles; first and unfinished cycles excluded. |
| successful_cycles | int64 | simulated | Completed cycles with no lost demand between consecutive receipts. |
| days | int64 | simulated | Number of replay dates for the KPI row. |
| fill_rate | double | simulated | Fulfilled units / demand proxy; null for zero demand. |
| cycle_service_level | double | simulated | Successful completed cycles / completed cycles; null if none completed. |
| inventory_turnover | double | simulated | Annualized fulfilled units / average inventory; unit proxy, not financial COGS turnover. |
| baseline_cost | double | simulated | Paired baseline total cost at the same item-store-service-scenario-run. |
| baseline_lost_sales_value | double | simulated | Paired baseline unfulfilled units valued at origin price. |
| estimated_cost_reduction | double | simulated | Baseline cost minus current policy cost; negative means worse scenario cost. |
| estimated_revenue_protected | double | simulated | Baseline lost-sales value minus current policy lost-sales value; scenario only. |

## m5_by_category_id
| Field | Type | Provenance | Definition |
|---|---|---|---|
| category_id | string | observed | M5 category natural key. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |
| mean_series_day_units | double | derived | Mean recorded demand over item-store-day observations in a group. |
| series_days | int64 | derived | Number of item-store-day observations in the summary denominator. |

## m5_by_department_id
| Field | Type | Provenance | Definition |
|---|---|---|---|
| department_id | string | observed | M5 department natural key. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |
| mean_series_day_units | double | derived | Mean recorded demand over item-store-day observations in a group. |
| series_days | int64 | derived | Number of item-store-day observations in the summary denominator. |

## m5_by_event_name
| Field | Type | Provenance | Definition |
|---|---|---|---|
| event_name | string | observed | First source calendar event name; nullable. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |
| mean_series_day_units | double | derived | Mean recorded demand over item-store-day observations in a group. |
| series_days | int64 | derived | Number of item-store-day observations in the summary denominator. |

## m5_by_item_id
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |
| mean_series_day_units | double | derived | Mean recorded demand over item-store-day observations in a group. |
| series_days | int64 | derived | Number of item-store-day observations in the summary denominator. |

## m5_by_month
| Field | Type | Provenance | Definition |
|---|---|---|---|
| month | int64 | derived | Calendar month 1–12. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |
| mean_series_day_units | double | derived | Mean recorded demand over item-store-day observations in a group. |
| series_days | int64 | derived | Number of item-store-day observations in the summary denominator. |

## m5_by_snap_flag
| Field | Type | Provenance | Definition |
|---|---|---|---|
| snap_flag | int64 | observed | Source state-specific SNAP eligibility indicator, 0 or 1; not a promotion flag. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |
| mean_series_day_units | double | derived | Mean recorded demand over item-store-day observations in a group. |
| series_days | int64 | derived | Number of item-store-day observations in the summary denominator. |

## m5_by_state_id
| Field | Type | Provenance | Definition |
|---|---|---|---|
| state_id | string | observed | M5 state code CA, TX or WI. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |
| mean_series_day_units | double | derived | Mean recorded demand over item-store-day observations in a group. |
| series_days | int64 | derived | Number of item-store-day observations in the summary denominator. |

## m5_by_store_id
| Field | Type | Provenance | Definition |
|---|---|---|---|
| store_id | string | observed | M5 store natural key. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |
| mean_series_day_units | double | derived | Mean recorded demand over item-store-day observations in a group. |
| series_days | int64 | derived | Number of item-store-day observations in the summary denominator. |

## m5_by_weekday
| Field | Type | Provenance | Definition |
|---|---|---|---|
| weekday | int64 | derived | Calendar weekday with Sunday=0, Monday=1, Saturday=6. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |
| mean_series_day_units | double | derived | Mean recorded demand over item-store-day observations in a group. |
| series_days | int64 | derived | Number of item-store-day observations in the summary denominator. |

## price_demand_association
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| store_id | string | observed | M5 store natural key. |
| price_change_demand_correlation | double | derived | Pearson correlation of daily percentage price change and recorded units; descriptive, not causal. |

## product_store_performance
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| store_id | string | observed | M5 store natural key. |
| category_id | string | observed | M5 category natural key. |
| department_id | string | observed | M5 department natural key. |
| state_id | string | observed | M5 state code CA, TX or WI. |
| average_daily_demand | double | derived | Trailing 90-day pre-origin recorded-sales mean for an item-store. |
| demand_std | double | derived | Sample standard deviation of trailing 90-day recorded sales. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| zero_demand_share | double | derived | Fraction of trailing item-store days with zero recorded sales. |
| last_price | double | derived | Most recent non-null price known at the summary or forecast origin. |
| abc | string | derived | Revenue concentration class using prior cumulative share: A <80%, B <95%, C remainder. |
| coefficient_of_variation | double | derived | Sample demand standard deviation / mean; null for zero mean. |
| xyz | string | derived | Variability class based on configured CV thresholds; high zero frequency forces Z. |
| abc_xyz | string | derived | Concatenated ABC and XYZ planning segment, e.g. A-X. |
| volume_segment | string | derived | Low/medium/high thirds of training mean-demand percentile rank. |
| cumulative_revenue_share | double | derived | Running revenue contribution in descending revenue order, including current pair. |

## recommendations
| Field | Type | Provenance | Definition |
|---|---|---|---|
| domain | string | derived | M5 or DataCo; domains must never be combined as one retailer. |
| evidence_type | string | derived | Historical, forecast evaluation, or simulated scenario evidence category. |
| recommendation | string | derived | Proposed action inferred from computed metrics; requires operational validation. |
| evidence | string | derived | Calculated metric and denominator supporting the proposed action. |
| source_table | string | derived | Exact analytical table containing the evidence for the recommendation. |
| data_provenance | string | derived | synthetic_fixture or kaggle; never substitute one for the other. |

## refresh_metadata
| Field | Type | Provenance | Definition |
|---|---|---|---|
| last_refresh_utc | string | derived | UTC timestamp captured after result generation, not current viewing time. |
| data_provenance | string | derived | synthetic_fixture or kaggle; never substitute one for the other. |
| mode | string | derived | Configured sample or full execution scope. |

## sales_daily
| Field | Type | Provenance | Definition |
|---|---|---|---|
| series_id | string | observed | M5 source series identifier including source split suffix. |
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| department_id | string | observed | M5 department natural key. |
| category_id | string | observed | M5 category natural key. |
| state_id | string | observed | M5 state code CA, TX or WI. |
| d | string | observed | M5 day label d_N joined to calendar. |
| date | date32[day] | observed | Calendar date represented by the observation or prediction. |
| date_key | int32 | derived | Integer YYYYMMDD key derived from calendar date. |
| units_sold | int64 | observed | M5 recorded sales units; availability-censored demand is possible. |
| sell_price | double | observed | M5 listed weekly item-store selling price, source currency per unit. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |
| wm_yr_wk | int64 | observed | M5 retail calendar week identifier. |
| weekday | int64 | derived | Calendar weekday with Sunday=0, Monday=1, Saturday=6. |
| month | int64 | derived | Calendar month 1–12. |
| quarter | int64 | derived | Calendar quarter 1–4. |
| event_name | string | observed | First source calendar event name; nullable. |
| event_type | string | observed | First source calendar event type; nullable. |
| event_name_2 | string | observed | Second source calendar event name; nullable. |
| event_type_2 | string | observed | Second source calendar event type; nullable. |
| snap_flag | int64 | observed | Source state-specific SNAP eligibility indicator, 0 or 1; not a promotion flag. |
| event_flag | int32 | derived | 1 if either source event is present on the date. |
| weekend_flag | int32 | derived | 1 for Saturday/Sunday, otherwise 0. |
| month_start_flag | int32 | derived | 1 on the first calendar day of a month. |
| month_end_flag | int32 | derived | 1 on the last calendar day of a month. |
| zero_sales_flag | int32 | derived | 1 if recorded units_sold equals zero. |
| store_id | string | observed | M5 store natural key. |
| year | int64 | derived | Calendar year. |

## sales_monthly
| Field | Type | Provenance | Definition |
|---|---|---|---|
| period | timestamp[us] | derived | Start date of the displayed daily, weekly or monthly aggregate. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |

## sales_trend
| Field | Type | Provenance | Definition |
|---|---|---|---|
| period | timestamp[us] | derived | Start date of the displayed daily, weekly or monthly aggregate. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |

## sales_weekly
| Field | Type | Provenance | Definition |
|---|---|---|---|
| period | timestamp[us] | derived | Start date of the displayed daily, weekly or monthly aggregate. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |

## stockout_risk
| Field | Type | Provenance | Definition |
|---|---|---|---|
| item_id | string | observed | M5 item natural key; not a DataCo product identifier. |
| store_id | string | observed | M5 store natural key. |
| category_id | string | observed | M5 category natural key. |
| department_id | string | observed | M5 department natural key. |
| state_id | string | observed | M5 state code CA, TX or WI. |
| average_daily_demand | double | derived | Trailing 90-day pre-origin recorded-sales mean for an item-store. |
| demand_std | double | derived | Sample standard deviation of trailing 90-day recorded sales. |
| revenue | double | derived | M5 recorded units times weekly price; zero-unit rows have zero revenue even with no price. |
| units_sold | double | observed | M5 recorded sales units; availability-censored demand is possible. |
| zero_demand_share | double | derived | Fraction of trailing item-store days with zero recorded sales. |
| last_price | double | derived | Most recent non-null price known at the summary or forecast origin. |
| supplier_id | string | simulated | SIM_ plus M5 category; illustrative supplier group, never real Walmart supplier. |
| average_lead_time_days | int64 | simulated | Assumed expected replenishment lead time in days. |
| lead_time_standard_deviation | double | simulated | Assumed lead-time standard deviation in days. |
| ordering_cost_per_order | double | simulated | Assumed fixed currency cost each time a purchase order is placed. |
| annual_holding_cost_rate | double | simulated | Annual holding cost as fraction of assumed unit cost. |
| estimated_unit_cost | double | simulated | Assumed cost-to-price ratio times last known price, with positive floor. |
| target_service_level | double | simulated | Scenario cycle-service target in (0,1); does not equal fill rate. |
| initial_inventory | int64 | simulated | Assumed opening on-hand units before first simulation demand. |
| review_period_days | int64 | simulated | Number of calendar days between ordering reviews. |
| lost_sale_penalty | double | simulated | Assumed cost per unfulfilled unit; not guaranteed lost revenue. |
| minimum_order_quantity | int64 | simulated | Smallest nonzero purchase quantity before pack rounding. |
| case_pack_size | int64 | simulated | Order quantities must be integer multiples of this positive unit count. |
| assumption_type | string | simulated | Explicit simulated_not_walmart provenance label. |
| seed | int64 | simulated | Fixed pseudo-random seed for reproducible assumption generation. |
| forecast_daily_demand | double | forecast | Mean predicted daily units over the planning horizon. |
| forecast_error_std | double | derived | Sample standard deviation of pre-test selected-model forecast residuals per item-store. |
| as_of_date | timestamp[ns] | derived | Snapshot date at which an inventory recommendation was generated. |
| safety_stock | double | simulated | Normal-approximation lead-time buffer units based on assumed service level. |
| expected_lead_time_demand | double | simulated | Forecast daily mean multiplied by mean lead days. |
| reorder_point | double | simulated | Expected lead-time demand plus lead-time safety stock; continuous-review reference. |
| protection_safety_stock | double | simulated | Safety units covering lead time plus periodic review interval. |
| order_up_to_level | double | simulated | Forecast mean times lead-plus-review days plus protection safety stock. |
| eoq | double | simulated | Square root of 2 × annualized units × fixed ordering cost / annual per-unit holding cost. |
| days_of_supply | double | simulated | Assumed initial inventory / forecast daily mean; undefined for zero mean. |
| inventory_value | double | simulated | Assumed initial stock multiplied by estimated unit cost. |
| demand_uncertainty_std | double | simulated | Forecast-error SD used for inventory policy, falling back to raw demand SD if unavailable. |
| stockout_probability | double | simulated | Normal lead-time demand tail above initial stock assuming no initial incoming POs. |
| recommended_order_quantity | int64 | simulated | Larger of EOQ or target shortage, rounded to MOQ/case pack, zero if no shortage. |
| excess_units | double | simulated | Positive initial inventory above protection order-up-to target. |
| excess_value | double | simulated | Excess units multiplied by estimated unit cost. |
