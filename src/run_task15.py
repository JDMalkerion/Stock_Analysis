import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "stocks.db")
SQL_DIR = os.path.join(BASE_DIR, "sql")


def print_table(headers, rows, col_widths):
    header_str = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
    sep_str = "-+-".join("-" * w for w in col_widths)
    print(header_str)
    print(sep_str)
    for row in rows:
        print(" | ".join(f"{str(val):<{w}}" for val, w in zip(row, col_widths)))


def run_task15():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    filepath = os.path.join(SQL_DIR, "15_adjusted_signals_all.sql")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split the file by semicolon into distinct queries
    statements = [s.strip() for s in content.split(";") if s.strip()]

    # 1. Buys and Sells per stock per version
    print("=" * 70)
    print("1. BUYS AND SELLS PER STOCK PER VERSION")
    print("=" * 70)
    cursor.execute(statements[0])
    rows_counts = cursor.fetchall()
    headers_counts = [desc[0] for desc in cursor.description]
    print_table(headers_counts, rows_counts, [14, 12, 10, 10])

    # 2. Every date where raw and adjusted signals differ
    print("\n" + "=" * 70)
    print("2. DATES WHERE RAW AND ADJUSTED SIGNALS DIFFER")
    print("=" * 70)
    cursor.execute(statements[1])
    rows_diff = cursor.fetchall()
    headers_diff = [desc[0] for desc in cursor.description]
    print_table(headers_diff, rows_diff, [14, 14, 14, 14])

    # 3. Last non-Hold signal per stock and version
    print("\n" + "=" * 70)
    print("3. LAST NON-HOLD SIGNAL PER STOCK AND VERSION")
    print("=" * 70)
    cursor.execute(statements[2])
    rows_last = cursor.fetchall()
    headers_last = [desc[0] for desc in cursor.description]
    print_table(headers_last, rows_last, [14, 12, 18, 14])

    conn.close()


if __name__ == "__main__":
    run_task15()
