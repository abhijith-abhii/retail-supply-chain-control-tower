# Assumptions and limitations

All inventory fields are simulated, never actual Walmart procurement or stock records. Editable defaults live in config/project_config.yaml; real-data runs persist per-pair assumptions to config/inventory_assumptions.csv and reuse supplied overrides. The shipped config CSV includes explicitly simulated synthetic-pair examples. Fixture runs export their assumptions separately and never overwrite this file. Real runs apply only matching item-store overrides, then persist the actual selected cohort’s simulated assumptions.

| Assumption | Default | Reason / sensitivity |
|---|---:|---|
| Seed | 42 | Deterministic, stable sorted pair order |
| Supplier | SIM_ + category | Illustrative grouping, not real supplier mapping |
| Mean lead days | integer uniform 3–10 | Broad illustrative local replenishment range; 0.5×/1.5× |
| Lead-time SD | 1.5 days | Nonzero uncertainty; 0.5×/1.5× |
| Fixed order cost | 25 source-currency units | Illustrative administration cost; 0.5×/1.5× |
| Annual holding rate | 25% | Illustrative capital/storage/spoilage burden; 0.5×/1.5× |
| Unit cost | 65% of last known price, floor 0.01 | Cost proxy, not measured margin; replace before decisions |
| Target cycle service | 95% | Compared with 90% and 98%; not equivalent to fill rate |
| Starting stock | ceil(14 × trailing mean demand) | Common comparison opening state; unknown real inventory |
| Review period | 7 days | Weekly review example |
| Lost-sale penalty | 40% of last-known price | Illustrative lost contribution/service cost, not full revenue; sensitivity |
| Minimum quantity | 6 units | Illustrative lot restriction |
| Case pack | 6 units | Illustrative packaging |
| Initial POs | none | Unknown true procurement pipeline |
| Lead-time law | rounded normal, minimum 1 day | Tail approximation; no correlated disruptions |
| Forecast price | last observed | No assumed future promotion/price plan |
| Simulation scope | first 100 sorted pairs maximum | Configurable runtime limit; sensitivity first 24; export counts disclose scope |

Sales censoring, missing real inventory, lack of supplier observations and simplified order policies limit operational validity. EOQ assumes stationary annualized demand and ignores capacity, spoilage, volume discounts and multi-item constraints. Normal safety stock can be unsuitable for intermittent demand; empirical lead-time error quantiles are a future improvement. Error autocorrelation and demand/lead-time correlation are not included. Monte Carlo estimates with three runs are demonstration-grade, not precision estimates. No causal cost savings or delivery root causes are established.

The raw Kaggle sources were not available when this project was built. Included executed results are synthetic-fixture validation. Real sample/full findings remain pending until authenticated files are supplied and processed. Dataset licenses and competition access terms must be checked by the downloader. Raw data and credentials must not be committed.
