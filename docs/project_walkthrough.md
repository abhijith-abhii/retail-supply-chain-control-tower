# Demonstration walkthrough

1. Open README and state the two independent data domains and inventory limitations (30 seconds).
2. Show raw-file detection and the no-PII allowlist; inspect audit summaries, never raw customer records (60 seconds).
3. Explain the daily M5 grain, weekly-price join and duplicate-key failure behavior using architecture.md (45 seconds).
4. Show rolling-origin dates, shifted features, recursive forecasts and frozen future prices. Compare all models at the same level; state the actual selected model from the run manifest (90 seconds).
5. Show stock assumptions, 95% policy, case rounding and a single pair's daily balance. Change service level and compare cost/fill rate, including negative outcomes (90 seconds).
6. Explain why DataCo order counts differ from order-line counts. Show eligible-order denominators and line-to-order profit aggregation (60 seconds).
7. Walk through six Power BI wireframes and demonstrate implemented Desktop pages only if you have built and reconciled them (60 seconds).
8. Close with one evidence-backed recommendation, its uncertainty, and the real data needed before deployment (30 seconds).

For every demo identify fixture versus Kaggle data up front. Treat notebooks as investigations over exported tables, not a second undocumented implementation of the pipeline.
