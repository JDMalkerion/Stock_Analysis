import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "stocks.db")
SQL_DIR = os.path.join(BASE_DIR, "sql")

STOCK_TABLE_MAP = {
    "Bajaj Auto": "bajaj_auto",
    "Eicher Motors": "eicher_motors",
    "Hero Motocorp": "hero_motocorp",
    "Infosys": "infosys",
    "TCS": "tcs",
    "TVS Motors": "tvs_motors",
}


def print_table(headers, rows, col_widths):
    header_str = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
    sep_str = "-+-".join("-" * w for w in col_widths)
    print(header_str)
    print(sep_str)
    for row in rows:
        print(" | ".join(f"{str(val):<{w}}" for val, w in zip(row, col_widths)))


def run_part3():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # TASK 11
    print("=" * 70)
    print("TASK 11: Percentage Change from First to Last Date (sql/11_pct_change.sql)")
    print("=" * 70)
    filepath_11 = os.path.join(SQL_DIR, "11_pct_change.sql")
    with open(filepath_11, "r", encoding="utf-8") as f:
        query_11 = f.read()

    cursor.execute(query_11)
    rows_11 = cursor.fetchall()
    headers_11 = [desc[0] for desc in cursor.description]
    print_table(headers_11, rows_11, [16, 14, 14, 12])

    # TASK 12
    print("\n" + "=" * 70)
    print("TASK 12: Single Worst Day per Stock (sql/12_worst_day.sql)")
    print("=" * 70)
    filepath_12 = os.path.join(SQL_DIR, "12_worst_day.sql")
    with open(filepath_12, "r", encoding="utf-8") as f:
        query_12 = f.read()

    cursor.execute(query_12)
    rows_12 = cursor.fetchall()
    headers_12 = [desc[0] for desc in cursor.description]
    print_table(headers_12, rows_12, [16, 14, 14, 12])

    # Context window for the two stocks with largest drops
    top_two = rows_12[:2]
    print("\n" + "=" * 70)
    print("SURROUNDING TRADING DAYS (3 BEFORE & 3 AFTER) FOR TOP 2 LARGEST DROPS")
    print("=" * 70)

    for stock, worst_date, close_price, pct_move in top_two:
        table_name = STOCK_TABLE_MAP[stock]
        print(f"\nStock: {stock} (Worst Date: {worst_date}, Close: {close_price}, Pct Move: {pct_move}%)")
        print(f"Source Table: {table_name}")

        # 3 trading days before
        cursor.execute(
            f"SELECT date, close_price, no_of_shares FROM {table_name} WHERE date < ? ORDER BY date DESC LIMIT 3;",
            (worst_date,),
        )
        before_rows = cursor.fetchall()[::-1]

        # Worst date row
        cursor.execute(
            f"SELECT date, close_price, no_of_shares FROM {table_name} WHERE date = ?;",
            (worst_date,),
        )
        worst_rows = cursor.fetchall()

        # 3 trading days after
        cursor.execute(
            f"SELECT date, close_price, no_of_shares FROM {table_name} WHERE date > ? ORDER BY date ASC LIMIT 3;",
            (worst_date,),
        )
        after_rows = cursor.fetchall()

        all_window_rows = []
        for r in before_rows:
            all_window_rows.append((r[0], r[1], r[2], "3 Days Before" if r == before_rows[0] else ("2 Days Before" if r == before_rows[1] else "1 Day Before")))
        for r in worst_rows:
            all_window_rows.append((r[0], r[1], r[2], "★ Worst Day"))
        for idx, r in enumerate(after_rows):
            all_window_rows.append((r[0], r[1], r[2], f"{idx+1} Day{'s' if idx > 0 else ''} After"))

        print_table(["date", "close_price", "no_of_shares", "relative_position"], all_window_rows, [14, 14, 14, 18])

    conn.close()


if __name__ == "__main__":
    run_part3()
