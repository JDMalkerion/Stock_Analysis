import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "stocks.db")
SQL_DIR = os.path.join(BASE_DIR, "sql")


def run_task10():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 70)
    print("STEP-BY-STEP CTE VALIDATION (LIMIT 20 OF EACH)")
    print("=" * 70)

    # 1. prices CTE
    q_prices = """
    WITH prices AS (
        SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto
        UNION ALL
        SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors
        UNION ALL
        SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp
        UNION ALL
        SELECT 'Infosys' AS stock, date, close_price FROM infosys
        UNION ALL
        SELECT 'TCS' AS stock, date, close_price FROM tcs
        UNION ALL
        SELECT 'TVS Motors' AS stock, date, close_price FROM tvs_motors
    )
    SELECT stock, date, close_price FROM prices LIMIT 20;
    """
    cursor.execute(q_prices)
    rows_prices = cursor.fetchall()
    print("\n--- 1. CTE: prices (LIMIT 20) ---")
    for r in rows_prices:
        print(f"  {r}")

    # Check row count of prices CTE
    cursor.execute("""
    WITH prices AS (
        SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto
        UNION ALL
        SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors
        UNION ALL
        SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp
        UNION ALL
        SELECT 'Infosys' AS stock, date, close_price FROM infosys
        UNION ALL
        SELECT 'TCS' AS stock, date, close_price FROM tcs
        UNION ALL
        SELECT 'TVS Motors' AS stock, date, close_price FROM tvs_motors
    )
    SELECT COUNT(*) FROM prices;
    """)
    prices_count = cursor.fetchone()[0]
    print(f"\nRow count of prices CTE: {prices_count} (Expect: 5334)")

    # 2. ma CTE
    q_ma = """
    WITH prices AS (
        SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto
        UNION ALL
        SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors
        UNION ALL
        SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp
        UNION ALL
        SELECT 'Infosys' AS stock, date, close_price FROM infosys
        UNION ALL
        SELECT 'TCS' AS stock, date, close_price FROM tcs
        UNION ALL
        SELECT 'TVS Motors' AS stock, date, close_price FROM tvs_motors
    ),
    ma AS (
        SELECT
            stock,
            date,
            close_price,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 20
                THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
                ELSE NULL
            END AS ma20,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 50
                THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)
                ELSE NULL
            END AS ma50
        FROM prices
    )
    SELECT stock, date, close_price, ma20, ma50 FROM ma ORDER BY stock, date LIMIT 20;
    """
    cursor.execute(q_ma)
    rows_ma = cursor.fetchall()
    print("\n--- 2. CTE: ma (LIMIT 20) ---")
    for r in rows_ma:
        print(f"  {r}")

    # 3. lagged CTE
    q_lagged = """
    WITH prices AS (
        SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto
        UNION ALL
        SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors
        UNION ALL
        SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp
        UNION ALL
        SELECT 'Infosys' AS stock, date, close_price FROM infosys
        UNION ALL
        SELECT 'TCS' AS stock, date, close_price FROM tcs
        UNION ALL
        SELECT 'TVS Motors' AS stock, date, close_price FROM tvs_motors
    ),
    ma AS (
        SELECT
            stock,
            date,
            close_price,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 20
                THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
                ELSE NULL
            END AS ma20,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 50
                THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)
                ELSE NULL
            END AS ma50
        FROM prices
    ),
    lagged AS (
        SELECT
            stock,
            date,
            close_price,
            ma20,
            ma50,
            LAG(ma20) OVER (PARTITION BY stock ORDER BY date) AS prev_ma20,
            LAG(ma50) OVER (PARTITION BY stock ORDER BY date) AS prev_ma50
        FROM ma
    )
    SELECT stock, date, close_price, ma20, ma50, prev_ma20, prev_ma50 FROM lagged ORDER BY stock, date LIMIT 20;
    """
    cursor.execute(q_lagged)
    rows_lagged = cursor.fetchall()
    print("\n--- 3. CTE: lagged (LIMIT 20) ---")
    for r in rows_lagged:
        print(f"  {r}")

    # 4. sig CTE
    q_sig = """
    WITH prices AS (
        SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto
        UNION ALL
        SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors
        UNION ALL
        SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp
        UNION ALL
        SELECT 'Infosys' AS stock, date, close_price FROM infosys
        UNION ALL
        SELECT 'TCS' AS stock, date, close_price FROM tcs
        UNION ALL
        SELECT 'TVS Motors' AS stock, date, close_price FROM tvs_motors
    ),
    ma AS (
        SELECT
            stock,
            date,
            close_price,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 20
                THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
                ELSE NULL
            END AS ma20,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 50
                THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)
                ELSE NULL
            END AS ma50
        FROM prices
    ),
    lagged AS (
        SELECT
            stock,
            date,
            close_price,
            ma20,
            ma50,
            LAG(ma20) OVER (PARTITION BY stock ORDER BY date) AS prev_ma20,
            LAG(ma50) OVER (PARTITION BY stock ORDER BY date) AS prev_ma50
        FROM ma
    ),
    sig AS (
        SELECT
            stock,
            date,
            close_price,
            CASE
                WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
                WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
                WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
                ELSE 'Hold'
            END AS `signal`
        FROM lagged
    )
    SELECT stock, date, close_price, `signal` FROM sig ORDER BY stock, date LIMIT 20;
    """
    cursor.execute(q_sig)
    rows_sig = cursor.fetchall()
    print("\n--- 4. CTE: sig (LIMIT 20) ---")
    for r in rows_sig:
        print(f"  {r}")

    # 5. latest CTE
    q_latest = """
    WITH prices AS (
        SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto
        UNION ALL
        SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors
        UNION ALL
        SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp
        UNION ALL
        SELECT 'Infosys' AS stock, date, close_price FROM infosys
        UNION ALL
        SELECT 'TCS' AS stock, date, close_price FROM tcs
        UNION ALL
        SELECT 'TVS Motors' AS stock, date, close_price FROM tvs_motors
    ),
    ma AS (
        SELECT
            stock,
            date,
            close_price,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 20
                THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
                ELSE NULL
            END AS ma20,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 50
                THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)
                ELSE NULL
            END AS ma50
        FROM prices
    ),
    lagged AS (
        SELECT
            stock,
            date,
            close_price,
            ma20,
            ma50,
            LAG(ma20) OVER (PARTITION BY stock ORDER BY date) AS prev_ma20,
            LAG(ma50) OVER (PARTITION BY stock ORDER BY date) AS prev_ma50
        FROM ma
    ),
    sig AS (
        SELECT
            stock,
            date,
            close_price,
            CASE
                WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
                WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
                WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
                ELSE 'Hold'
            END AS `signal`
        FROM lagged
    ),
    latest AS (
        SELECT
            stock,
            date AS last_signal_date,
            `signal` AS last_signal,
            ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date DESC) AS rn
        FROM sig
        WHERE `signal` != 'Hold'
    )
    SELECT stock, last_signal_date, last_signal, rn FROM latest ORDER BY stock, rn LIMIT 20;
    """
    cursor.execute(q_latest)
    rows_latest = cursor.fetchall()
    print("\n--- 5. CTE: latest (LIMIT 20) ---")
    for r in rows_latest:
        print(f"  {r}")

    # FINAL QUERY FROM sql/10_all_stocks.sql
    print("\n" + "=" * 70)
    print("FINAL QUERY: sql/10_all_stocks.sql (Unrounded MA)")
    print("=" * 70)
    filepath_10 = os.path.join(SQL_DIR, "10_all_stocks.sql")
    with open(filepath_10, "r", encoding="utf-8") as f:
        query_10 = f.read()

    cursor.execute(query_10)
    final_rows = cursor.fetchall()
    headers = [desc[0] for desc in cursor.description]

    # Print nicely formatted table
    col_widths = [16, 8, 8, 8, 18, 14]
    header_str = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
    sep_str = "-+-".join("-" * w for w in col_widths)
    print(header_str)
    print(sep_str)
    for row in final_rows:
        print(" | ".join(f"{str(val):<{w}}" for val, w in zip(row, col_widths)))

    # Sums of buys, sells, and holds across all six stocks
    total_buys = sum(row[1] for row in final_rows)
    total_sells = sum(row[2] for row in final_rows)
    total_holds = sum(row[3] for row in final_rows)
    print(f"\nTotal Buys across all stocks : {total_buys}")
    print(f"Total Sells across all stocks: {total_sells}")
    print(f"Total Holds across all stocks: {total_holds}")

    # Cross-check Bajaj Auto with task 8 and task 7
    print("\n" + "=" * 70)
    print("CROSS-CHECKS: Bajaj Auto")
    print("=" * 70)
    cursor.execute("SELECT `signal`, COUNT(*) FROM bajaj2 GROUP BY `signal`;")
    bajaj2_counts = dict(cursor.fetchall())
    expected_bajaj_buys = bajaj2_counts.get("Buy", 0)
    expected_bajaj_sells = bajaj2_counts.get("Sell", 0)
    expected_bajaj_holds = bajaj2_counts.get("Hold", 0)

    cursor.execute("SELECT date, `signal` FROM bajaj2 WHERE `signal` != 'Hold' ORDER BY date DESC LIMIT 1;")
    bajaj2_last_non_hold = cursor.fetchone()

    bajaj_row = next(r for r in final_rows if r[0] == "Bajaj Auto")
    print(f"Task 10 Bajaj Auto row: stock={bajaj_row[0]}, buys={bajaj_row[1]}, sells={bajaj_row[2]}, holds={bajaj_row[3]}, last_signal_date={bajaj_row[4]}, last_signal={bajaj_row[5]}")
    print(f"Task 8 Task/DB counts : Buy={expected_bajaj_buys}, Sell={expected_bajaj_sells}, Hold={expected_bajaj_holds}")
    print(f"Task 7 Last non-Hold  : date={bajaj2_last_non_hold[0]}, signal={bajaj2_last_non_hold[1]}")

    match_counts = (bajaj_row[1] == expected_bajaj_buys == 12) and (bajaj_row[2] == expected_bajaj_sells == 11) and (bajaj_row[3] == expected_bajaj_holds == 866)
    match_last_sig = (bajaj_row[4] == bajaj2_last_non_hold[0]) and (bajaj_row[5] == bajaj2_last_non_hold[1])
    print(f"Cross-check buys/sells/holds match: {'PASS' if match_counts else 'FAIL'}")
    print(f"Cross-check last signal match: {'PASS' if match_last_sig else 'FAIL'}")

    # Query with ROUND(..., 2)
    print("\n" + "=" * 70)
    print("COMPARISON: Final query with ROUND(..., 2) in ma CTE")
    print("=" * 70)
    q_rounded = """
    WITH prices AS (
        SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto
        UNION ALL
        SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors
        UNION ALL
        SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp
        UNION ALL
        SELECT 'Infosys' AS stock, date, close_price FROM infosys
        UNION ALL
        SELECT 'TCS' AS stock, date, close_price FROM tcs
        UNION ALL
        SELECT 'TVS Motors' AS stock, date, close_price FROM tvs_motors
    ),
    ma AS (
        SELECT
            stock,
            date,
            close_price,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 20
                THEN ROUND(AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 2)
                ELSE NULL
            END AS ma20,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 50
                THEN ROUND(AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW), 2)
                ELSE NULL
            END AS ma50
        FROM prices
    ),
    lagged AS (
        SELECT
            stock,
            date,
            close_price,
            ma20,
            ma50,
            LAG(ma20) OVER (PARTITION BY stock ORDER BY date) AS prev_ma20,
            LAG(ma50) OVER (PARTITION BY stock ORDER BY date) AS prev_ma50
        FROM ma
    ),
    sig AS (
        SELECT
            stock,
            date,
            close_price,
            CASE
                WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
                WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
                WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
                ELSE 'Hold'
            END AS `signal`
        FROM lagged
    ),
    latest AS (
        SELECT
            stock,
            date AS last_signal_date,
            `signal` AS last_signal,
            ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date DESC) AS rn
        FROM sig
        WHERE `signal` != 'Hold'
    )
    SELECT
        s.stock,
        SUM(CASE WHEN s.`signal` = 'Buy' THEN 1 ELSE 0 END) AS buys,
        SUM(CASE WHEN s.`signal` = 'Sell' THEN 1 ELSE 0 END) AS sells,
        SUM(CASE WHEN s.`signal` = 'Hold' THEN 1 ELSE 0 END) AS holds,
        l.last_signal_date,
        l.last_signal
    FROM sig s
    JOIN latest l ON s.stock = l.stock AND l.rn = 1
    GROUP BY s.stock, l.last_signal_date, l.last_signal
    ORDER BY s.stock;
    """
    cursor.execute(q_rounded)
    rounded_rows = cursor.fetchall()

    print("Rounded Results:")
    for row in rounded_rows:
        print(f"  {row}")

    diffs = []
    for unrounded_row, rounded_row in zip(final_rows, rounded_rows):
        if unrounded_row != rounded_row:
            diffs.append((unrounded_row, rounded_row))

    if not diffs:
        print("\nResult: No buys or sells counts change between unrounded and rounded (..., 2).")
    else:
        print(f"\nResult: Differences found in {len(diffs)} stocks:")
        for u, r in diffs:
            print(f"  Unrounded: {u} vs Rounded: {r}")

    conn.close()


if __name__ == "__main__":
    run_task10()
