import duckdb
import os

# Make paths robust to where the script is executed from.
# dbt profile expects the DuckDB file at `./data/pa_warehouse.duckdb`.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "data", "pa_warehouse.duckdb"))
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "data"))

TABLES = {
    "pa_requests":  "pa_requests.csv",
    "payers":       "payers.csv",
    "procedures":   "procedures.csv",
    "providers":    "providers.csv",
}

def main():
    print(f"Connecting to {DB_PATH} ...")
    con = duckdb.connect(DB_PATH)

    print("Creating raw schema ...")
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    for table_name, filename in TABLES.items():
        path = os.path.join(DATA_DIR, filename)
        print(f"\nLoading raw.{table_name} from {filename} ...")

        con.execute(f"DROP TABLE IF EXISTS raw.{table_name}")
        con.execute(f"""
            CREATE TABLE raw.{table_name} AS
            SELECT * FROM read_csv_auto('{path}', header=True)
        """)

        count = con.execute(f"SELECT COUNT(*) FROM raw.{table_name}").fetchone()[0]
        cols  = con.execute(f"DESCRIBE raw.{table_name}").fetchdf()
        print(f"  Rows    : {count:,}")
        print(f"  Columns : {list(cols['column_name'])}")

    print("\n── Schema summary ──────────────────────────────")
    tables = con.execute("""
        SELECT table_name, estimated_size
        FROM duckdb_tables()
        WHERE schema_name = 'raw'
        ORDER BY table_name
    """).fetchdf()
    print(tables.to_string(index=False))

    print("\n── Quick validation ────────────────────────────")
    checks = [
        ("Total PA requests",        "SELECT COUNT(*) FROM raw.pa_requests"),
        ("Distinct payers",          "SELECT COUNT(DISTINCT payer_id) FROM raw.pa_requests"),
        ("Distinct procedure codes", "SELECT COUNT(DISTINCT procedure_code) FROM raw.pa_requests"),
        ("Status breakdown", """
            SELECT status, COUNT(*) AS cnt,
                   ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(),1) AS pct
            FROM raw.pa_requests
            GROUP BY status
            ORDER BY cnt DESC
        """),
        ("SLA breaches",             "SELECT COUNT(*) FROM raw.pa_requests WHERE sla_breach_flag = true"),
        ("Pending approaching SLA",  "SELECT COUNT(*) FROM raw.pa_requests WHERE approaching_breach = true"),
    ]

    for label, sql in checks:
        result = con.execute(sql).fetchdf()
        print(f"\n{label}:")
        print(result.to_string(index=False))

    con.close()
    print(f"\nDone. Warehouse saved to {DB_PATH}")
    print("Open in DBeaver: File > New Connection > DuckDB > point to this .duckdb file")

if __name__ == "__main__":
    main()