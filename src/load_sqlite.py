import csv
import os
import sqlite3
from datetime import datetime

# File to table mapping
FILE_TABLE_MAP = {
    "Bajaj Auto.csv": "bajaj_auto",
    "Eicher Motors.csv": "eicher_motors",
    "Hero Motocorp.csv": "hero_motocorp",
    "Infosys.csv": "infosys",
    "TCS.csv": "tcs",
    "TVS Motors.csv": "tvs_motors",
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "stocks.db")

CREATE_TABLE_TEMPLATE = """
DROP TABLE IF EXISTS {table_name};
CREATE TABLE {table_name} (
    date TEXT,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    wap REAL,
    no_of_shares INTEGER,
    no_of_trades INTEGER,
    total_turnover REAL,
    deliverable_qty INTEGER,
    pct_deli_qty REAL,
    spread_high_low REAL,
    spread_close_open REAL
);
"""

INSERT_TEMPLATE = """
INSERT INTO {table_name} (
    date,
    open_price,
    high_price,
    low_price,
    close_price,
    wap,
    no_of_shares,
    no_of_trades,
    total_turnover,
    deliverable_qty,
    pct_deli_qty,
    spread_high_low,
    spread_close_open
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""


def parse_date(date_str):
    cleaned = date_str.strip()
    if not cleaned:
        return None
    return datetime.strptime(cleaned, "%d-%B-%Y").strftime("%Y-%m-%d")


def parse_float(val_str):
    cleaned = val_str.strip()
    if not cleaned:
        return None
    return float(cleaned)


def parse_int(val_str):
    cleaned = val_str.strip()
    if not cleaned:
        return None
    return int(float(cleaned))


def load_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for filename, table_name in FILE_TABLE_MAP.items():
        csv_path = os.path.join(DATA_DIR, filename)
        print(f"Loading {filename} into {table_name}...")

        # Recreate table (idempotent)
        cursor.executescript(CREATE_TABLE_TEMPLATE.format(table_name=table_name))

        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)  # skip header row

            rows_to_insert = []
            for row in reader:
                # Map CSV columns to table columns:
                # 0: Date -> date
                # 1: Open Price -> open_price
                # 2: High Price -> high_price
                # 3: Low Price -> low_price
                # 4: Close Price -> close_price
                # 5: WAP -> wap
                # 6: No.of Shares -> no_of_shares
                # 7: No. of Trades -> no_of_trades
                # 8: Total Turnover (Rs.) -> total_turnover
                # 9: Deliverable Quantity -> deliverable_qty
                # 10: % Deli. Qty to Traded Qty -> pct_deli_qty
                # 11: Spread High-Low -> spread_high_low
                # 12: Spread Close-Open -> spread_close_open (trimmed)

                date_val = parse_date(row[0])
                open_price = parse_float(row[1])
                high_price = parse_float(row[2])
                low_price = parse_float(row[3])
                close_price = parse_float(row[4])
                wap = parse_float(row[5])
                no_of_shares = parse_int(row[6])
                no_of_trades = parse_int(row[7])
                total_turnover = parse_float(row[8])
                deliverable_qty = parse_int(row[9])
                pct_deli_qty = parse_float(row[10])
                spread_high_low = parse_float(row[11])
                spread_close_open = parse_float(row[12])

                rows_to_insert.append((
                    date_val,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    wap,
                    no_of_shares,
                    no_of_trades,
                    total_turnover,
                    deliverable_qty,
                    pct_deli_qty,
                    spread_high_low,
                    spread_close_open,
                ))

            cursor.executemany(INSERT_TEMPLATE.format(table_name=table_name), rows_to_insert)
            print(f"Inserted {len(rows_to_insert)} rows into {table_name}.")

    conn.commit()
    conn.close()
    print("Database load completed successfully.")


if __name__ == "__main__":
    load_data()
