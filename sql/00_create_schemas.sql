CREATE SCHEMA IF NOT EXISTS common;
CREATE SCHEMA IF NOT EXISTS m5;
CREATE SCHEMA IF NOT EXISTS dataco;
CREATE SCHEMA IF NOT EXISTS mart;
COMMENT ON SCHEMA m5 IS 'M5 retail sales and simulated inventory. No DataCo transactions.';
COMMENT ON SCHEMA dataco IS 'Independent DataCo operational domain; customer PII excluded.';
