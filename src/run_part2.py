import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "stocks.db")
SQL_DIR = os.path.join(BASE_DIR, "sql")


def execute_sql_file(cursor, filename):
    filepath = os.path.join(SQL_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()
    cursor.executescript(sql)


def run_part2():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # TASK 5: bajaj1
    print("=" * 60)
    print("TASK 5: Running sql/05_moving_averages.sql...")
    execute_sql_file(cursor, "05_moving_averages.sql")

    cursor.execute("PRAGMA table_info(bajaj1);")
    bajaj1_cols = [row[1] for row in cursor.fetchall()]
    cursor.execute("SELECT COUNT(*) FROM bajaj1;")
    bajaj1_count = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM bajaj1 WHERE ma20 IS NOT NULL ORDER BY date LIMIT 1;")
    first_ma20 = cursor.fetchone()

    cursor.execute("SELECT * FROM bajaj1 WHERE ma50 IS NOT NULL ORDER BY date LIMIT 1;")
    first_ma50 = cursor.fetchone()

    cursor.execute("SELECT * FROM bajaj1 WHERE date = '2018-07-31';")
    bajaj1_20180731 = cursor.fetchone()

    print(f"bajaj1 Row Count: {bajaj1_count}")
    print(f"bajaj1 Column Names: {bajaj1_cols}")
    print(f"First row where ma20 IS NOT NULL: {first_ma20}")
    print(f"First row where ma50 IS NOT NULL: {first_ma50}")
    print(f"Row for 2018-07-31: {bajaj1_20180731}")

    # TASK 6: master_table
    print("=" * 60)
    print("TASK 6: Check and create master_table...")

    # Pre-creation check: bajaj_auto joined to tcs on date count
    cursor.execute("SELECT COUNT(*) FROM bajaj_auto b JOIN tcs ON b.date = tcs.date;")
    pre_check_count = cursor.fetchone()[0]
    print(f"Pre-check COUNT(*) bajaj_auto JOIN tcs on date: {pre_check_count} (Expect: 889)")
    assert pre_check_count == 889, f"Expected 889, got {pre_check_count}"

    print("Running sql/06_master_table.sql...")
    execute_sql_file(cursor, "06_master_table.sql")

    cursor.execute("PRAGMA table_info(master_table);")
    master_cols = [row[1] for row in cursor.fetchall()]
    cursor.execute("SELECT COUNT(*) FROM master_table;")
    master_count = cursor.fetchone()[0]

    # NULL check across any column
    null_conditions = " OR ".join([f"{col} IS NULL" for col in master_cols])
    cursor.execute(f"SELECT COUNT(*) FROM master_table WHERE {null_conditions};")
    null_count = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM master_table WHERE date = '2018-07-31';")
    master_20180731 = cursor.fetchone()

    print(f"master_table Row Count: {master_count}")
    print(f"master_table Column Names: {master_cols}")
    print(f"Number of NULLs in any column: {null_count}")
    print(f"Row for 2018-07-31: {master_20180731}")

    # TASK 7: bajaj2
    print("=" * 60)
    print("TASK 7: Running sql/07_signals.sql...")
    execute_sql_file(cursor, "07_signals.sql")

    cursor.execute("PRAGMA table_info(bajaj2);")
    bajaj2_cols = [row[1] for row in cursor.fetchall()]
    cursor.execute("SELECT COUNT(*) FROM bajaj2;")
    bajaj2_count = cursor.fetchone()[0]

    cursor.execute("SELECT date FROM bajaj2 WHERE `signal` = 'Buy' ORDER BY date LIMIT 1;")
    first_buy_date = cursor.fetchone()[0]

    cursor.execute("SELECT date FROM bajaj2 WHERE `signal` = 'Sell' ORDER BY date LIMIT 1;")
    first_sell_date = cursor.fetchone()[0]

    print(f"bajaj2 Row Count: {bajaj2_count}")
    print(f"bajaj2 Column Names: {bajaj2_cols}")
    print(f"Date of first Buy : {first_buy_date}")
    print(f"Date of first Sell: {first_sell_date}")

    # TASK 8: signal counts
    print("=" * 60)
    print("TASK 8: Running sql/08_signal_counts.sql...")
    filepath_08 = os.path.join(SQL_DIR, "08_signal_counts.sql")
    with open(filepath_08, "r", encoding="utf-8") as f:
        query_08 = f.read()
    cursor.execute(query_08)
    signal_counts = cursor.fetchall()
    total_signal_count = sum(row[1] for row in signal_counts)

    print("Signal Counts:")
    for sig, cnt in signal_counts:
        print(f"  {sig}: {cnt}")
    print(f"Sum of counts: {total_signal_count}")

    # TASK 9: signal on date
    print("=" * 60)
    print("TASK 9: Running sql/09_signal_on_date.sql and test dates...")
    filepath_09 = os.path.join(SQL_DIR, "09_signal_on_date.sql")
    with open(filepath_09, "r", encoding="utf-8") as f:
        query_09 = f.read()

    cursor.execute(query_09)
    res_20180621 = cursor.fetchone()
    print(f"Output for 2018-06-21 (from 09_signal_on_date.sql): date={res_20180621[0]}, signal={res_20180621[1]}")

    test_dates = ["2015-05-18", "2016-01-04"]
    for t_date in test_dates:
        cursor.execute("SELECT date, `signal` FROM bajaj2 WHERE date = ?;", (t_date,))
        res = cursor.fetchone()
        print(f"Output for {t_date} (test date): date={res[0]}, signal={res[1]}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    run_part2()
