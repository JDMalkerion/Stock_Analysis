import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "stocks.db")
SQL_DIR = os.path.join(BASE_DIR, "sql")

SQL_FILES = [
    "01_history.sql",
    "02_eicher_top5.sql",
    "03_tcs_yearly.sql",
    "04_null_deliverable.sql",
]


def run_checks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for sql_file in SQL_FILES:
        filepath = os.path.join(SQL_DIR, sql_file)
        with open(filepath, "r", encoding="utf-8") as f:
            query = f.read().strip()

        print("=" * 60)
        print(f"Running: {sql_file}")
        print("Query:")
        print(query)
        print("-" * 60)

        cursor.execute(query)
        col_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        print(f"Columns: {col_names}")
        print("Results:")
        for row in rows:
            print(f"  {row}")
        print(f"Total Rows: {len(rows)}")

    conn.close()


if __name__ == "__main__":
    run_checks()
