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


def run_task16():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    filepath = os.path.join(SQL_DIR, "16_whipsaws.sql")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into statements
    statements = [s.strip() for s in content.split(";") if s.strip()]

    # 1. Per stock: consecutive-signal pairs with a gap of 30 days or less
    print("=" * 80)
    print("1. NUMBER OF CONSECUTIVE-SIGNAL PAIRS WITH A GAP <= 30 DAYS PER STOCK")
    print("=" * 80)
    cursor.execute(statements[0])
    rows_q1 = cursor.fetchall()
    headers_q1 = [desc[0] for desc in cursor.description]
    print_table(headers_q1, rows_q1, [16, 26])

    # 2. Per stock: round trips (Buy followed by Sell) summary & details
    print("\n" + "=" * 80)
    print("2. ROUND TRIPS (BUY FOLLOWED BY SELL) SUMMARY PER STOCK")
    print("=" * 80)
    cursor.execute(statements[1])
    rows_q2_summary = cursor.fetchall()
    headers_q2_summary = [desc[0] for desc in cursor.description]
    print_table(headers_q2_summary, rows_q2_summary, [16, 12, 10, 16, 20, 22])

    print("\n--- Detailed Round Trips (Every Buy followed by Sell) ---")
    cursor.execute(statements[2])
    rows_q2_details = cursor.fetchall()
    headers_q2_details = [desc[0] for desc in cursor.description]
    print_table(headers_q2_details, rows_q2_details, [14, 12, 12, 12, 12, 10, 10])

    # 3. 5 shortest-gap signal pairs across all stocks
    print("\n" + "=" * 80)
    print("3. TOP 5 SHORTEST-GAP SIGNAL PAIRS ACROSS ALL STOCKS")
    print("=" * 80)
    cursor.execute(statements[3])
    rows_q3 = cursor.fetchall()
    headers_q3 = [desc[0] for desc in cursor.description]
    print_table(headers_q3, rows_q3, [14, 12, 12, 12, 12, 8, 12, 10])

    conn.close()


if __name__ == "__main__":
    run_task16()
