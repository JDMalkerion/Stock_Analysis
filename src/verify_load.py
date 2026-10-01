import os
import sqlite3

TABLES = [
    "bajaj_auto",
    "eicher_motors",
    "hero_motocorp",
    "infosys",
    "tcs",
    "tvs_motors",
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "stocks.db")


def verify_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for table in TABLES:
        print("=" * 60)
        print(f"Table: {table}")

        # Get column names
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [row[1] for row in cursor.fetchall()]

        # Row count, min date, max date
        cursor.execute(f"SELECT COUNT(*), MIN(date), MAX(date) FROM {table};")
        row_count, min_date, max_date = cursor.fetchone()
        print(f"  Row Count : {row_count} (Expect: 889)")
        print(f"  MIN(date) : {min_date} (Expect: 2015-01-01)")
        print(f"  MAX(date) : {max_date} (Expect: 2018-07-31)")

        # NULL counts per column
        null_counts = {}
        for col in columns:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL;")
            null_counts[col] = cursor.fetchone()[0]

        print("  NULL counts per column:")
        for col, cnt in null_counts.items():
            print(f"    - {col}: {cnt}")

    conn.close()


if __name__ == "__main__":
    verify_database()
