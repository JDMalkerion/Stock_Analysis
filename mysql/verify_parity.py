#!/usr/bin/env python3
import decimal
import os
import sqlite3
import sys
import pymysql


def load_env(env_path):
    env = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip("'\"")
    return env


def compare_values(v_lite, v_my, tol=0.01):
    if v_lite is None and v_my is None:
        return True
    if v_lite is None or v_my is None:
        return False

    # Normalize dates
    if hasattr(v_my, "strftime"):
        v_my = v_my.strftime("%Y-%m-%d")

    # If both are numeric
    if isinstance(v_lite, (int, float)) and isinstance(v_my, (int, float, decimal.Decimal)):
        if isinstance(v_lite, int) and isinstance(v_my, int):
            return v_lite == v_my
        # Using 1e-6 epsilon for float representation of 0.01
        return abs(float(v_lite) - float(v_my)) <= (tol + 1e-6)

    # Fallback to string comparison
    return str(v_lite).strip() == str(v_my).strip()


def run_parity():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    sqlite_db_path = os.path.join(project_root, "data", "stocks.db")
    env = load_env(os.path.join(script_dir, ".env"))

    db_name = sys.argv[1] if len(sys.argv) > 1 else env.get("MYSQL_DATABASE", "stock_analysis")

    lite_conn = sqlite3.connect(sqlite_db_path)
    lite_cur = lite_conn.cursor()

    my_conn = pymysql.connect(
        host=env.get("MYSQL_HOST", "127.0.0.1"),
        port=int(env.get("MYSQL_PORT", 3306)),
        user=env.get("MYSQL_USER", "root"),
        password=env.get("MYSQL_ROOT_PASSWORD", ""),
        database=db_name,
    )
    my_cur = my_conn.cursor()

    total_diffs = 0

    def check_parity(name, lite_query, my_query):
        nonlocal total_diffs
        print(f"\nChecking parity: {name} ...")
        lite_cur.execute(lite_query)
        lite_rows = lite_cur.fetchall()
        my_cur.execute(my_query)
        my_rows = my_cur.fetchall()

        if len(lite_rows) != len(my_rows):
            print(f"  [ROW COUNT MISMATCH] SQLite: {len(lite_rows)} rows vs MySQL: {len(my_rows)} rows")
            total_diffs += 1
            return

        diff_count = 0
        for i, (r_lite, r_my) in enumerate(zip(lite_rows, my_rows)):
            if len(r_lite) != len(r_my):
                print(f"  [COLUMN COUNT MISMATCH] Row {i}: SQLite len={len(r_lite)} vs MySQL len={len(r_my)}")
                diff_count += 1
                continue

            for col_idx, (vl, vm) in enumerate(zip(r_lite, r_my)):
                if not compare_values(vl, vm):
                    print(f"  [DIFF] Task={name}, Row={i}, Col={col_idx}: SQLite={vl!r} (full: {vl}) vs MySQL={vm!r} (full: {vm})")
                    diff_count += 1

        if diff_count == 0:
            print(f"  [PASS] {name}: all {len(lite_rows)} rows match perfectly.")
        else:
            print(f"  [FAIL] {name}: {diff_count} difference(s) found.")
            total_diffs += diff_count

    # 1. bajaj1 table
    check_parity(
        "bajaj1 (all rows)",
        "SELECT date, close_price, ma20, ma50 FROM bajaj1 ORDER BY date;",
        "SELECT `date`, close_price, ma20, ma50 FROM bajaj1 ORDER BY `date`;",
    )

    # 2. master_table table
    check_parity(
        "master_table (all rows)",
        "SELECT date, bajaj, tcs, tvs, infosys, eicher, hero FROM master_table ORDER BY date;",
        "SELECT `date`, bajaj, tcs, tvs, infosys, eicher, hero FROM master_table ORDER BY `date`;",
    )

    # 3. bajaj2 table
    check_parity(
        "bajaj2 (all rows)",
        "SELECT date, close_price, `signal` FROM bajaj2 ORDER BY date;",
        "SELECT `date`, close_price, `signal` FROM bajaj2 ORDER BY `date`;",
    )

    # 4. Task 8: signal counts
    check_parity(
        "Task 8: signal counts",
        "SELECT `signal`, COUNT(*) FROM bajaj2 GROUP BY `signal` ORDER BY `signal`;",
        "SELECT `signal`, COUNT(*) FROM bajaj2 GROUP BY `signal` ORDER BY `signal`;",
    )

    # 5. Task 10: all stocks signals
    sql_10_lite = open(os.path.join(project_root, "sql", "10_all_stocks.sql")).read()
    check_parity(
        "Task 10: all stocks signal counts",
        sql_10_lite,
        sql_10_lite,
    )

    # 6. Task 11: pct change
    sql_11_lite = open(os.path.join(project_root, "sql", "11_pct_change.sql")).read()
    check_parity(
        "Task 11: percentage change",
        sql_11_lite,
        sql_11_lite,
    )

    # 7. Task 12: single worst day
    sql_12_lite = open(os.path.join(project_root, "sql", "12_worst_day.sql")).read()
    check_parity(
        "Task 12: single worst day",
        sql_12_lite,
        sql_12_lite,
    )

    # 8. Task 13: corporate action adjusted return
    sql_13_lite = open(os.path.join(project_root, "sql", "13_adjusted.sql")).read()
    check_parity(
        "Task 13: adjusted return",
        sql_13_lite,
        sql_13_lite,
    )

    # 9. Task 15: three result sets
    sql_15_lite = open(os.path.join(project_root, "sql", "15_adjusted_signals_all.sql")).read()
    q15_statements = [s.strip() for s in sql_15_lite.split(";") if s.strip()]

    # In MySQL, Task 15 averages are unrounded per port rules
    q15_lite_unrounded = [
        s.replace("ROUND(AVG(close_price) OVER (PARTITION BY stock, version ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 2)",
                  "AVG(close_price) OVER (PARTITION BY stock, version ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)")
         .replace("ROUND(AVG(close_price) OVER (PARTITION BY stock, version ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW), 2)",
                  "AVG(close_price) OVER (PARTITION BY stock, version ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)")
        for s in q15_statements
    ]

    check_parity(
        "Task 15 (Set 1): Buys and Sells counts",
        q15_lite_unrounded[0],
        q15_lite_unrounded[0],
    )
    check_parity(
        "Task 15 (Set 2): Differing dates",
        q15_lite_unrounded[1],
        q15_lite_unrounded[1],
    )
    check_parity(
        "Task 15 (Set 3): Last signal",
        q15_lite_unrounded[2],
        q15_lite_unrounded[2],
    )

    # 10. Task 16: summary, round-trip list, and shortest-pairs
    sql_16_lite = open(os.path.join(project_root, "sql", "16_whipsaws.sql")).read()
    q16_statements = [s.strip() for s in sql_16_lite.split(";") if s.strip()]

    # SQLite query 2 is summary, query 3 is detailed round trips, query 4 is shortest pairs
    # In MySQL, julianday(date) - julianday(prev_date) -> DATEDIFF(date, prev_date)
    q16_summary_my = (
        q16_statements[1]
        .replace("CAST(ROUND(julianday(date) - julianday(LAG(date) OVER (PARTITION BY stock ORDER BY date))) AS INTEGER)",
                 "DATEDIFF(`date`, LAG(`date`) OVER (PARTITION BY stock ORDER BY `date`))")
    )
    check_parity(
        "Task 16: Round trips summary",
        q16_statements[1],
        q16_summary_my,
    )

    q16_details_my = (
        q16_statements[2]
        .replace("CAST(ROUND(julianday(date) - julianday(LAG(date) OVER (PARTITION BY stock ORDER BY date))) AS INTEGER)",
                 "DATEDIFF(`date`, LAG(`date`) OVER (PARTITION BY stock ORDER BY `date`))")
    )
    check_parity(
        "Task 16: Round trip list",
        q16_statements[2],
        q16_details_my,
    )

    import re
    q16_shortest_my = (
        q16_statements[3]
        .replace("CAST(ROUND(julianday(date) - julianday(prev_date)) AS INTEGER)",
                 "DATEDIFF(`date`, prev_date)")
    )
    q16_shortest_my = re.sub(r"\)\s*WHERE prev_date IS NOT NULL", ") s_inner WHERE prev_date IS NOT NULL", q16_shortest_my)
    check_parity(
        "Task 16: Top 5 shortest-gap pairs",
        q16_statements[3],
        q16_shortest_my,
    )

    lite_conn.close()
    my_conn.close()

    print("\n" + "=" * 60)
    if total_diffs == 0:
        print("OVERALL PARITY STATUS: 100% PASS (Zero differences)")
    else:
        print(f"OVERALL PARITY STATUS: FAIL ({total_diffs} differences)")
        sys.exit(1)


if __name__ == "__main__":
    run_parity()
