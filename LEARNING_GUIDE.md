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

1. **What problem does this project solve, and what is its unit of work?** Explain explore business performance and inventory tradeoffs, identify operations managers as the audience, and trace one concrete example through the files above. Use the demonstration output rather than hypothetical impact.
2. **Why did you choose the first design decision?** Extend the existing repository's fixture and analysis rather than counting it as a second project. Show the corresponding implementation and a test that would fail if that property were removed.
3. **How do you protect correctness when inputs or execution change?** Use an explicit ingestion allowlist so privacy-test fields never enter dashboard calculations or exports. Explain the relevant invalid-input or edge-case test and distinguish a checked property from an untested assumption.
4. **How do you make results inspectable and reproducible?** Compute late-delivery rate at distinct-order grain while summing revenue/profit at line grain. Point to actual outputs and recorded commands. Explain why a successful example is weaker evidence than a tested boundary or independently reconciled total.
5. **What would you improve before real deployment or real-data use?** Synthetic DataCo-shaped fixture. The new browser dashboard is separate from the older forecasting pipeline and unverified native Power BI plans. Real Kaggle data and native PBIX remain optional unfinished extensions, not completed deliverables. Choose one limitation, describe the missing evidence, and propose a measurable acceptance check rather than promising production readiness.

## Independent exercise

Add a shipping-mode filter and test that order-level delivery metrics do not double count multi-line orders.

Write down the expected behavior before editing. Add a meaningful regression check, run the existing suite, and describe what changed in your own words.

## Contribution and resume guidance

The implementation was developed with substantial AI assistance under Abhijith Viswanathan's direction. The verified contribution is the working artifact and the learning work actually completed, not invented employment or adoption.

Suggested factual bullet after personally validating the demo:

- Implemented and validated explore business performance and inventory tradeoffs using Python · SQLite · browser, with existing analytics and documented correctness checks and limitations.

Use [VERIFICATION.md](VERIFICATION.md) to add only measured numbers. Do not claim production traffic, users, savings, upstream acceptance or cloud deployment without corresponding evidence.
