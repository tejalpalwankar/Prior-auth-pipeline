import duckdb
import os
import pandas as pd

DB_PATH    = "data/pa_warehouse.duckdb"
EXPORT_DIR = "data/tableau_exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

con = duckdb.connect(DB_PATH, read_only=True)

exports = {
    "fct_pa_requests":        "SELECT * FROM analytics_marts.fct_pa_requests",
    "dim_payer_summary":      "SELECT * FROM analytics_marts.dim_payer_summary",
    "dim_procedure_summary":  "SELECT * FROM analytics_marts.dim_procedure_summary",
    "mart_weekly_compliance": "SELECT * FROM analytics_marts.mart_weekly_compliance",
    "mart_sla_watch":         "SELECT * FROM analytics_marts.mart_sla_watch",
}

print("Exporting mart tables for Tableau...\n")
for name, sql in exports.items():
    df = con.execute(sql).fetchdf()
    path = f"{EXPORT_DIR}/{name}.csv"
    df.to_csv(path, index=False)
    print(f"  {name}.csv  →  {len(df):,} rows  ·  {df.shape[1]} columns")

con.close()
print(f"\nAll files saved to {EXPORT_DIR}/")
print("Next: open Tableau Public and connect to these CSV files.")
