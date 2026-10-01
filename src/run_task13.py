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


def run_task13():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # TASK 13
    print("=" * 70)
    print("TASK 13: Adjusted Percentage Change (sql/13_adjusted.sql)")
    print("=" * 70)
    filepath_13 = os.path.join(SQL_DIR, "13_adjusted.sql")
    with open(filepath_13, "r", encoding="utf-8") as f:
        query_13 = f.read()

    cursor.execute(query_13)
    rows_13 = cursor.fetchall()
    headers_13 = [desc[0] for desc in cursor.description]
    print_table(headers_13, rows_13, [16, 22])

    # CLIFF CHECK FOR TASK 13
    print("\n" + "=" * 70)
    print("CLIFF CHECK: 3 TRADING DAYS BEFORE AND AFTER EVENT DATES")
    print("=" * 70)

    events = [
        ("TCS", "tcs", "2018-05-31"),
        ("Infosys", "infosys", "2015-06-15"),
    ]

    for stock_name, table_name, event_date in events:
        print(f"\nStock: {stock_name} (Event Date: {event_date})")

        # 3 days before
        cursor.execute(
            f"SELECT date, close_price, close_price / 2.0 AS adj_close FROM {table_name} WHERE date < ? ORDER BY date DESC LIMIT 3;",
            (event_date,),
        )
        before = cursor.fetchall()[::-1]

        # Event date
        cursor.execute(
            f"SELECT date, close_price, close_price AS adj_close FROM {table_name} WHERE date = ?;",
            (event_date,),
        )
        event_row = cursor.fetchall()

        # 3 days after
        cursor.execute(
            f"SELECT date, close_price, close_price AS adj_close FROM {table_name} WHERE date > ? ORDER BY date ASC LIMIT 3;",
            (event_date,),
        )
        after = cursor.fetchall()

        window_rows = []
        for r in before:
            window_rows.append((r[0], r[1], round(r[2], 3), "Before Event (close / 2)"))
        for r in event_row:
            window_rows.append((r[0], r[1], round(r[2], 3), "★ Event Date (New Level)"))
        for r in after:
            window_rows.append((r[0], r[1], round(r[2], 3), "After Event (New Level)"))

        print_table(["date", "raw_close", "adj_close", "note"], window_rows, [12, 12, 12, 28])

    # STRETCH TASK 14
    print("\n" + "=" * 70)
    print("STRETCH: TCS Raw vs Adjusted Signals (sql/14_tcs_adjusted_signals.sql)")
    print("=" * 70)
    filepath_14 = os.path.join(SQL_DIR, "14_tcs_adjusted_signals.sql")
    with open(filepath_14, "r", encoding="utf-8") as f:
        content_14 = f.read()

    # Split into the two standalone queries by semicolon
    statements = [s.strip() for s in content_14.split(";") if s.strip()]

    # Statement 1: Signal counts per version
    cursor.execute(statements[0])
    counts_rows = cursor.fetchall()
    headers_counts = [desc[0] for desc in cursor.description]
    print("\n--- TCS Signal Counts by Version ---")
    print_table(headers_counts, counts_rows, [14, 10, 10])

    # Statement 2: Differing dates between versions
    cursor.execute(statements[1])
    diff_rows = cursor.fetchall()
    headers_diff = [desc[0] for desc in cursor.description]
    print("\n--- Dates with Differing Signals (Raw vs Adjusted) ---")
    if diff_rows:
        print_table(headers_diff, diff_rows, [14, 14, 14])
    else:
        print("  No differing dates found.")

    conn.close()


if __name__ == "__main__":
    run_task13()
