# Retail Control Tower — learning guide

## What it does

Explore business performance and inventory tradeoffs. The intended user is operations managers. Browser controls → validated Flask API → project analysis/workflow → results and export.

## Run and demonstrate

Follow the README installation block, then: Install requirements-dashboard.txt, run app.py and filter by market/month. Reconcile category totals to KPI totals and inspect the late-order denominator. See README_PIPELINE.md for the preserved larger analysis pipeline.

## Important files

- `app.py` — local HTTP interface and request/error handling.
- `core.py` — project-specific logic.
- `tests/` — regression and correctness checks.
- `reports/` — recorded outputs and verification evidence.

## Three engineering decisions

1. Extend the existing repository's fixture and analysis rather than counting it as a second project.
2. Use an explicit ingestion allowlist so privacy-test fields never enter dashboard calculations or exports.
3. Compute late-delivery rate at distinct-order grain while summing revenue/profit at line grain.

## Five interview questions

1. **Why distinguish lines from orders?** Revenue and profit are line-level quantities, while late-delivery rates count distinct orders. Using line counts as the denominator would overweight orders with more items.

2. **How do filters work?** The browser submits market, segment and month selections. The server validates them and recomputes metrics from the allowed sample columns.

3. **How are private fields kept out of responses?** The dashboard explicitly selects allowed fields rather than forwarding whole source records. Tests include privacy canaries to verify excluded names, emails and address-like values do not appear.

4. **What existing work was reused?** The repository’s data sample and earlier supply-chain analysis assets were preserved, then a lightweight interactive browser dashboard and focused tests were added. It is counted once.

5. **What is outside the finished demonstration?** The dashboard runs on synthetic sample data. Native Power BI and the full optional legacy forecasting pipeline were not revalidated as part of this dashboard release.

## Independent exercise

Add a shipping-mode filter and test that order-level delivery metrics do not double count multi-line orders.

Write down the expected behavior before editing. Add a meaningful regression check, run the existing suite, and describe what changed in your own words.

## Contribution and resume guidance

The implementation was developed with substantial AI assistance under Abhijith Viswanathan's direction. The verified contribution is the working artifact and the learning work actually completed, not invented employment or adoption.

Suggested factual bullet after personally validating the demo:

- Extended an existing supply-chain repository with a filtered business dashboard, distinct-order delivery metrics and field-level privacy checks on synthetic data.

Use [VERIFICATION.md](VERIFICATION.md) to add only measured numbers. Do not claim production traffic, users, savings, upstream acceptance or cloud deployment without corresponding evidence.
