# Data, code and model sources

The topic comes from the source mapping in the portfolio index. Original authored synthetic fixtures and procedural images are distributed under the repository MIT license. Synthetic records do not describe actual customers, employees, players or transactions.

Implementation references:
- Flask: https://flask.palletsprojects.com/en/stable/ — request handling and security considerations.
- Python SQLite: https://docs.python.org/3/library/sqlite3.html — transactions, parameter binding and authorizers.
- scikit-learn: https://scikit-learn.org/stable/common_pitfalls.html — leakage prevention and fitted preprocessing.

Only applicable libraries are used; their upstream licenses remain in installed distributions. Project code does not claim authorship of dependencies.

This dashboard reuses the repository’s authored synthetic fixture from `src/fixtures.py`, not downloaded Kaggle records. M5 and DataCo source plans and terms remain in the preserved pipeline documentation. No real-data findings or native PBIX are claimed. Privacy-test canaries in the raw synthetic fixture are explicitly excluded from the dashboard.
