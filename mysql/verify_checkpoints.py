#!/usr/bin/env python3
import os
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


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env = load_env(os.path.join(script_dir, ".env"))

    db_name = sys.argv[1] if len(sys.argv) > 1 else env.get("MYSQL_DATABASE", "stock_analysis")

    conn = pymysql.connect(
        host=env.get("MYSQL_HOST", "127.0.0.1"),
        port=int(env.get("MYSQL_PORT", 3306)),
        user=env.get("MYSQL_USER", "root"),
        password=env.get("MYSQL_ROOT_PASSWORD", ""),
        database=db_name,
    )
    cur = conn.cursor()

    overall_pass = True

    def check(desc, condition, detail=""):
        nonlocal overall_pass
        status = "PASS" if condition else "FAIL"
        if not condition:
            overall_pass = False
        msg = f"[{status}] {desc}"
        if detail:
            msg += f" ({detail})"
        print(msg)

    # T1: 889, 2015-01-01, 2018-07-31
    cur.execute("SELECT COUNT(*), MIN(`date`), MAX(`date`) FROM bajaj_auto;")
    c, mn, mx = cur.fetchone()
    check("T1: bajaj_auto count=889, min=2015-01-01, max=2018-07-31",
          c == 889 and str(mn) == "2015-01-01" and str(mx) == "2018-07-31",
          f"got count={c}, min={mn}, max={mx}")

    # T2: top close 32786.40 on 2017-09-07; all five dates in 2017-09
    cur.execute("SELECT `date`, close_price FROM eicher_motors ORDER BY close_price DESC LIMIT 5;")
    t2_rows = cur.fetchall()
    t2_top_date, t2_top_close = str(t2_rows[0][0]), float(t2_rows[0][1])
    all_in_sept_2017 = all(str(r[0]).startswith("2017-09") for r in t2_rows)
    check("T2: Eicher top close 32786.40 on 2017-09-07, all 5 dates in 2017-09",
          abs(t2_top_close - 32786.40) < 0.01 and t2_top_date == "2017-09-07" and all_in_sept_2017,
          f"got top={t2_top_close} on {t2_top_date}")

    # T3: 2015 2537.39 | 2016 2419.00 | 2017 2475.36 | 2018 2729.12
    cur.execute("SELECT YEAR(`date`) AS yr, ROUND(AVG(close_price), 2) FROM tcs GROUP BY yr ORDER BY yr;")
    t3_dict = {r[0]: float(r[1]) for r in cur.fetchall()}
    expected_t3 = {2015: 2537.39, 2016: 2419.00, 2017: 2475.36, 2018: 2729.12}
    t3_ok = all(abs(t3_dict.get(yr, 0) - exp) < 0.01 for yr, exp in expected_t3.items())
    check("T3: TCS yearly avg close 2015=2537.39, 2016=2419.00, 2017=2475.36, 2018=2729.12",
          t3_ok, f"got {t3_dict}")

    # T4: 6 rows on 2 dates (2015-12-09 x4, 2017-08-31 x2)
    cur.execute("""
        SELECT `date`, COUNT(*) FROM (
            SELECT 'bajaj_auto' AS stock, `date` FROM bajaj_auto WHERE deliverable_qty IS NULL
            UNION ALL SELECT 'eicher_motors', `date` FROM eicher_motors WHERE deliverable_qty IS NULL
            UNION ALL SELECT 'hero_motocorp', `date` FROM hero_motocorp WHERE deliverable_qty IS NULL
            UNION ALL SELECT 'infosys', `date` FROM infosys WHERE deliverable_qty IS NULL
            UNION ALL SELECT 'tcs', `date` FROM tcs WHERE deliverable_qty IS NULL
            UNION ALL SELECT 'tvs_motors', `date` FROM tvs_motors WHERE deliverable_qty IS NULL
        ) t GROUP BY `date` ORDER BY `date`;
    """)
    t4_counts = {str(r[0]): r[1] for r in cur.fetchall()}
    check("T4: NULL deliverable 6 rows on 2 dates (2015-12-09 x4, 2017-08-31 x2)",
          t4_counts.get("2015-12-09") == 4 and t4_counts.get("2017-08-31") == 2 and len(t4_counts) == 2,
          f"got {t4_counts}")

    # T5: bajaj1 889 rows; first ma20 row 2015-01-29 = 2415.53; first ma50 row 2015-03-13 = 2283.80; on 2018-07-31 ma20 2918.51, ma50 2866.88
    cur.execute("SELECT COUNT(*) FROM bajaj1;")
    b1_count = cur.fetchone()[0]
    cur.execute("SELECT `date`, ma20 FROM bajaj1 WHERE ma20 IS NOT NULL ORDER BY `date` LIMIT 1;")
    f_ma20_date, f_ma20_val = cur.fetchone()
    cur.execute("SELECT `date`, ma50 FROM bajaj1 WHERE ma50 IS NOT NULL ORDER BY `date` LIMIT 1;")
    f_ma50_date, f_ma50_val = cur.fetchone()
    cur.execute("SELECT ma20, ma50 FROM bajaj1 WHERE `date` = '2018-07-31';")
    last_ma20, last_ma50 = cur.fetchone()
    t5_ok = (b1_count == 889 and
             str(f_ma20_date) == "2015-01-29" and abs(float(f_ma20_val) - 2415.53) < 0.01 and
             str(f_ma50_date) == "2015-03-13" and abs(float(f_ma50_val) - 2283.80) < 0.01 and
             abs(float(last_ma20) - 2918.51) < 0.01 and abs(float(last_ma50) - 2866.88) < 0.01)
    check("T5: bajaj1 889 rows; first ma20 2015-01-29=2415.53, first ma50 2015-03-13=2283.80, 2018-07-31 ma20=2918.51 ma50=2866.88",
          t5_ok, f"b1_count={b1_count}, f20=({f_ma20_date},{f_ma20_val}), f50=({f_ma50_date},{f_ma50_val}), last=({last_ma20},{last_ma50})")

    # T6: master_table 889 rows, 7 columns, 0 NULLs; on 2018-07-31 bajaj 2700.70, tcs 1941.25, tvs 517.45, infosys 1365.00, eicher 27820.95, hero 3293.80
    cur.execute("SELECT COUNT(*) FROM master_table;")
    mt_count = cur.fetchone()[0]
    cur.execute("SHOW COLUMNS FROM master_table;")
    mt_cols = cur.fetchall()
    cur.execute("SELECT * FROM master_table WHERE `date` = '2018-07-31';")
    mt_row = cur.fetchone()
    # date, bajaj, tcs, tvs, infosys, eicher, hero
    cur.execute("""SELECT COUNT(*) FROM master_table WHERE
        `date` IS NULL OR bajaj IS NULL OR tcs IS NULL OR tvs IS NULL OR
        infosys IS NULL OR eicher IS NULL OR hero IS NULL;""")
    mt_nulls = cur.fetchone()[0]
    t6_ok = (mt_count == 889 and len(mt_cols) == 7 and mt_nulls == 0 and
             abs(float(mt_row[1]) - 2700.70) < 0.01 and
             abs(float(mt_row[2]) - 1941.25) < 0.01 and
             abs(float(mt_row[3]) - 517.45) < 0.01 and
             abs(float(mt_row[4]) - 1365.00) < 0.01 and
             abs(float(mt_row[5]) - 27820.95) < 0.01 and
             abs(float(mt_row[6]) - 3293.80) < 0.01)
    check("T6: master_table 889 rows, 7 cols, 0 NULLs; 2018-07-31 values match",
          t6_ok, f"mt_count={mt_count}, cols={len(mt_cols)}, nulls={mt_nulls}, row={mt_row}")

    # T7/T8: bajaj2 889 rows; first Buy 2015-05-18, first Sell 2015-08-24; Buy 12, Hold 866, Sell 11
    cur.execute("SELECT COUNT(*) FROM bajaj2;")
    b2_count = cur.fetchone()[0]
    cur.execute("SELECT `date` FROM bajaj2 WHERE `signal` = 'Buy' ORDER BY `date` LIMIT 1;")
    f_buy = str(cur.fetchone()[0])
    cur.execute("SELECT `date` FROM bajaj2 WHERE `signal` = 'Sell' ORDER BY `date` LIMIT 1;")
    f_sell = str(cur.fetchone()[0])
    cur.execute("SELECT `signal`, COUNT(*) FROM bajaj2 GROUP BY `signal`;")
    b2_counts = dict(cur.fetchall())
    t7_ok = (b2_count == 889 and f_buy == "2015-05-18" and f_sell == "2015-08-24" and
             b2_counts.get("Buy") == 12 and b2_counts.get("Hold") == 866 and b2_counts.get("Sell") == 11)
    check("T7/T8: bajaj2 889 rows; first Buy=2015-05-18, first Sell=2015-08-24; Buy=12, Hold=866, Sell=11",
          t7_ok, f"counts={b2_counts}, first_buy={f_buy}, first_sell={f_sell}")

    # T9: bajaj_signal('2015-05-18') Buy; ('2016-01-04') Hold; ('2018-06-21') Buy; ('2018-07-29', a Sunday) NULL
    cur.execute("SELECT bajaj_signal('2015-05-18'), bajaj_signal('2016-01-04'), bajaj_signal('2018-06-21'), bajaj_signal('2018-07-29');")
    sig_may15, sig_jan16, sig_jun18, sig_sun = cur.fetchone()
    t9_ok = (sig_may15 == "Buy" and sig_jan16 == "Hold" and sig_jun18 == "Buy" and sig_sun is None)
    check("T9: bajaj_signal('2015-05-18')=Buy, ('2016-01-04')=Hold, ('2018-06-21')=Buy, ('2018-07-29')=NULL",
          t9_ok, f"got {sig_may15}, {sig_jan16}, {sig_jun18}, {sig_sun}")

    # T10 (stock, buys, sells, holds, last date, last signal)
    # Totals 56 buys, 57 sells, 5221 holds
    cur.execute("""
    WITH prices AS (
        SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
        UNION ALL SELECT 'Eicher Motors', `date`, close_price FROM eicher_motors
        UNION ALL SELECT 'Hero Motocorp', `date`, close_price FROM hero_motocorp
        UNION ALL SELECT 'Infosys', `date`, close_price FROM infosys
        UNION ALL SELECT 'TCS', `date`, close_price FROM tcs
        UNION ALL SELECT 'TVS Motors', `date`, close_price FROM tvs_motors
    ),
    ma AS (
        SELECT stock, `date`, close_price,
            CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 20
                 THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma20,
            CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 50
                 THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma50
        FROM prices
    ),
    lagged AS (
        SELECT stock, `date`, close_price, ma20, ma50,
            LAG(ma20) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma20,
            LAG(ma50) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma50
        FROM ma
    ),
    sig AS (
        SELECT stock, `date`, close_price,
            CASE WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
                 WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
                 WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell' ELSE 'Hold' END AS `signal`
        FROM lagged
    ),
    latest AS (
        SELECT stock, `date` AS last_signal_date, `signal` AS last_signal,
            ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date` DESC) AS rn
        FROM sig WHERE `signal` != 'Hold'
    )
    SELECT s.stock,
        SUM(CASE WHEN s.`signal` = 'Buy' THEN 1 ELSE 0 END) AS buys,
        SUM(CASE WHEN s.`signal` = 'Sell' THEN 1 ELSE 0 END) AS sells,
        SUM(CASE WHEN s.`signal` = 'Hold' THEN 1 ELSE 0 END) AS holds,
        l.last_signal_date, l.last_signal
    FROM sig s JOIN latest l ON s.stock = l.stock AND l.rn = 1
    GROUP BY s.stock, l.last_signal_date, l.last_signal ORDER BY s.stock;
    """)
    t10_rows = cur.fetchall()
    t10_dict = {r[0]: (r[1], r[2], r[3], str(r[4]), r[5]) for r in t10_rows}
    expected_t10 = {
        "Bajaj Auto": (12, 11, 866, "2018-06-21", "Buy"),
        "Eicher Motors": (6, 7, 876, "2018-06-06", "Sell"),
        "Hero Motocorp": (9, 9, 871, "2018-05-22", "Sell"),
        "Infosys": (9, 9, 871, "2018-05-07", "Buy"),
        "TCS": (12, 13, 864, "2018-06-05", "Sell"),
        "TVS Motors": (8, 8, 873, "2018-05-17", "Sell"),
    }
    t10_ok = (t10_dict == expected_t10 and
              sum(r[1] for r in t10_rows) == 56 and
              sum(r[2] for r in t10_rows) == 57 and
              sum(r[3] for r in t10_rows) == 5221)
    check("T10: all stocks buys/sells/holds/last signal (totals 56 buys, 57 sells, 5221 holds)",
          t10_ok, f"got {t10_dict}")

    # T11 % change: TVS 86.9, Eicher 82.6, Bajaj 10.0, Hero 6.0, TCS -23.8, Infosys -30.9
    cur.execute("""
    WITH prices AS (
        SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
        UNION ALL SELECT 'Eicher Motors', `date`, close_price FROM eicher_motors
        UNION ALL SELECT 'Hero Motocorp', `date`, close_price FROM hero_motocorp
        UNION ALL SELECT 'Infosys', `date`, close_price FROM infosys
        UNION ALL SELECT 'TCS', `date`, close_price FROM tcs
        UNION ALL SELECT 'TVS Motors', `date`, close_price FROM tvs_motors
    ),
    ends AS (SELECT stock, MIN(`date`) AS f_date, MAX(`date`) AS l_date FROM prices GROUP BY stock)
    SELECT e.stock, ROUND(100.0 * (p_last.close_price - p_first.close_price) / p_first.close_price, 1) AS pct_change
    FROM ends e
    JOIN prices p_first ON e.stock = p_first.stock AND e.f_date = p_first.`date`
    JOIN prices p_last ON e.stock = p_last.stock AND e.l_date = p_last.`date`;
    """)
    t11_dict = {r[0]: float(r[1]) for r in cur.fetchall()}
    expected_t11 = {"TVS Motors": 86.9, "Eicher Motors": 82.6, "Bajaj Auto": 10.0, "Hero Motocorp": 6.0, "TCS": -23.8, "Infosys": -30.9}
    t11_ok = all(abs(t11_dict.get(s, 0) - exp) < 0.05 for s, exp in expected_t11.items())
    check("T11: % change TVS 86.9, Eicher 82.6, Bajaj 10.0, Hero 6.0, TCS -23.8, Infosys -30.9",
          t11_ok, f"got {t11_dict}")

    # T12 worst day: TCS 2018-05-31 -50.4; Infosys 2015-06-15 -49.9; TVS 2016-05-03 -9.7; Eicher 2015-08-24 -9.3; Bajaj 2015-08-24 -9.1; Hero 2018-07-23 -6.2
    cur.execute("""
    WITH prices AS (
        SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
        UNION ALL SELECT 'Eicher Motors', `date`, close_price FROM eicher_motors
        UNION ALL SELECT 'Hero Motocorp', `date`, close_price FROM hero_motocorp
        UNION ALL SELECT 'Infosys', `date`, close_price FROM infosys
        UNION ALL SELECT 'TCS', `date`, close_price FROM tcs
        UNION ALL SELECT 'TVS Motors', `date`, close_price FROM tvs_motors
    ),
    daily AS (SELECT stock, `date`, close_price, LAG(close_price) OVER (PARTITION BY stock ORDER BY `date`) AS prev_close FROM prices),
    moves AS (SELECT stock, `date`, 100.0 * (close_price / prev_close - 1) AS pct_move FROM daily WHERE prev_close IS NOT NULL),
    ranked AS (SELECT stock, `date`, pct_move, ROW_NUMBER() OVER (PARTITION BY stock ORDER BY pct_move ASC) AS rn FROM moves)
    SELECT stock, `date`, ROUND(pct_move, 1) FROM ranked WHERE rn = 1;
    """)
    t12_dict = {r[0]: (str(r[1]), float(r[2])) for r in cur.fetchall()}
    expected_t12 = {
        "TCS": ("2018-05-31", -50.4),
        "Infosys": ("2015-06-15", -49.9),
        "TVS Motors": ("2016-05-03", -9.7),
        "Eicher Motors": ("2015-08-24", -9.3),
        "Bajaj Auto": ("2015-08-24", -9.1),
        "Hero Motocorp": ("2018-07-23", -6.2),
    }
    t12_ok = all(t12_dict.get(s, ("", 0))[0] == exp[0] and abs(t12_dict.get(s, ("", 0))[1] - exp[1]) < 0.05 for s, exp in expected_t12.items())
    check("T12: worst day per stock dates and returns match",
          t12_ok, f"got {t12_dict}")

    # T13 adjusted % change: Infosys 38.2, TCS 52.4
    cur.execute("""
    WITH adjusted AS (
        SELECT 'TCS' AS stock, `date`, CASE WHEN `date` < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS adj_close FROM tcs
        UNION ALL
        SELECT 'Infosys' AS stock, `date`, CASE WHEN `date` < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS adj_close FROM infosys
    )
    SELECT stock, ROUND(100.0 * (MAX(CASE WHEN `date` = '2018-07-31' THEN adj_close END) - MAX(CASE WHEN `date` = '2015-01-01' THEN adj_close END)) / MAX(CASE WHEN `date` = '2015-01-01' THEN adj_close END), 1)
    FROM adjusted GROUP BY stock;
    """)
    t13_dict = {r[0]: float(r[1]) for r in cur.fetchall()}
    check("T13: adjusted % change Infosys=38.2, TCS=52.4",
          abs(t13_dict.get("Infosys", 0) - 38.2) < 0.05 and abs(t13_dict.get("TCS", 0) - 52.4) < 0.05,
          f"got {t13_dict}")

    # T14/T15 buys/sells: TCS raw 12/13, adjusted 12/12; Infosys raw 9/9, adjusted 10/10.
    # Differing dates: TCS 2018-06-05; Infosys 2015-07-01, 2015-07-08, 2015-07-27, 2015-08-18.
    # Last signal: TCS adjusted Buy 2018-04-20, TCS raw Sell 2018-06-05, Infosys Buy 2018-05-07 (both versions)
    cur.execute("""
    WITH combined_series AS (
        SELECT 'TCS' AS stock, 'raw' AS version, `date`, close_price FROM tcs
        UNION ALL SELECT 'TCS', 'adjusted', `date`, CASE WHEN `date` < '2018-05-31' THEN close_price / 2.0 ELSE close_price END FROM tcs
        UNION ALL SELECT 'Infosys', 'raw', `date`, close_price FROM infosys
        UNION ALL SELECT 'Infosys', 'adjusted', `date`, CASE WHEN `date` < '2015-06-15' THEN close_price / 2.0 ELSE close_price END FROM infosys
    ),
    ma AS (
        SELECT stock, version, `date`, close_price,
            CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY `date`) >= 20
                 THEN AVG(close_price) OVER (PARTITION BY stock, version ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma20,
            CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY `date`) >= 50
                 THEN AVG(close_price) OVER (PARTITION BY stock, version ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma50
        FROM combined_series
    ),
    lagged AS (
        SELECT stock, version, `date`, close_price, ma20, ma50,
            LAG(ma20) OVER (PARTITION BY stock, version ORDER BY `date`) AS prev_ma20,
            LAG(ma50) OVER (PARTITION BY stock, version ORDER BY `date`) AS prev_ma50
        FROM ma
    ),
    sig AS (
        SELECT stock, version, `date`, close_price,
            CASE WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
                 WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
                 WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell' ELSE 'Hold' END AS `signal`
        FROM lagged
    )
    SELECT stock, version, SUM(CASE WHEN `signal`='Buy' THEN 1 ELSE 0 END), SUM(CASE WHEN `signal`='Sell' THEN 1 ELSE 0 END)
    FROM sig GROUP BY stock, version;
    """)
    counts_15 = {(r[0], r[1]): (r[2], r[3]) for r in cur.fetchall()}
    t15_counts_ok = (counts_15.get(("TCS", "raw")) == (12, 13) and
                     counts_15.get(("TCS", "adjusted")) == (12, 12) and
                     counts_15.get(("Infosys", "raw")) == (9, 9) and
                     counts_15.get(("Infosys", "adjusted")) == (10, 10))

    cur.execute("""
    WITH combined_series AS (
        SELECT 'TCS' AS stock, 'raw' AS version, `date`, close_price FROM tcs
        UNION ALL SELECT 'TCS', 'adjusted', `date`, CASE WHEN `date` < '2018-05-31' THEN close_price / 2.0 ELSE close_price END FROM tcs
        UNION ALL SELECT 'Infosys', 'raw', `date`, close_price FROM infosys
        UNION ALL SELECT 'Infosys', 'adjusted', `date`, CASE WHEN `date` < '2015-06-15' THEN close_price / 2.0 ELSE close_price END FROM infosys
    ),
    ma AS (
        SELECT stock, version, `date`, close_price,
            CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY `date`) >= 20
                 THEN AVG(close_price) OVER (PARTITION BY stock, version ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma20,
            CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY `date`) >= 50
                 THEN AVG(close_price) OVER (PARTITION BY stock, version ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma50
        FROM combined_series
    ),
    lagged AS (
        SELECT stock, version, `date`, close_price, ma20, ma50,
            LAG(ma20) OVER (PARTITION BY stock, version ORDER BY `date`) AS prev_ma20,
            LAG(ma50) OVER (PARTITION BY stock, version ORDER BY `date`) AS prev_ma50
        FROM ma
    ),
    sig AS (
        SELECT stock, version, `date`, close_price,
            CASE WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
                 WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
                 WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell' ELSE 'Hold' END AS `signal`
        FROM lagged
    )
    SELECT r.stock, r.`date`
    FROM (SELECT stock, `date`, `signal` FROM sig WHERE version = 'raw') r
    JOIN (SELECT stock, `date`, `signal` FROM sig WHERE version = 'adjusted') a
      ON r.stock = a.stock AND r.`date` = a.`date`
    WHERE r.`signal` != a.`signal`
    ORDER BY r.stock, r.`date`;
    """)
    diff_dates = [(r[0], str(r[1])) for r in cur.fetchall()]
    expected_diffs = [
        ("Infosys", "2015-07-01"),
        ("Infosys", "2015-07-08"),
        ("Infosys", "2015-07-27"),
        ("Infosys", "2015-08-18"),
        ("TCS", "2018-06-05"),
    ]
    t15_diffs_ok = diff_dates == expected_diffs

    cur.execute("""
    WITH combined_series AS (
        SELECT 'TCS' AS stock, 'raw' AS version, `date`, close_price FROM tcs
        UNION ALL SELECT 'TCS', 'adjusted', `date`, CASE WHEN `date` < '2018-05-31' THEN close_price / 2.0 ELSE close_price END FROM tcs
        UNION ALL SELECT 'Infosys', 'raw', `date`, close_price FROM infosys
        UNION ALL SELECT 'Infosys', 'adjusted', `date`, CASE WHEN `date` < '2015-06-15' THEN close_price / 2.0 ELSE close_price END FROM infosys
    ),
    ma AS (
        SELECT stock, version, `date`, close_price,
            CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY `date`) >= 20
                 THEN AVG(close_price) OVER (PARTITION BY stock, version ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma20,
            CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY `date`) >= 50
                 THEN AVG(close_price) OVER (PARTITION BY stock, version ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma50
        FROM combined_series
    ),
    lagged AS (
        SELECT stock, version, `date`, close_price, ma20, ma50,
            LAG(ma20) OVER (PARTITION BY stock, version ORDER BY `date`) AS prev_ma20,
            LAG(ma50) OVER (PARTITION BY stock, version ORDER BY `date`) AS prev_ma50
        FROM ma
    ),
    sig AS (
        SELECT stock, version, `date`, close_price,
            CASE WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
                 WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
                 WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell' ELSE 'Hold' END AS `signal`
        FROM lagged
    ),
    ranked_signals AS (
        SELECT stock, version, `date`, `signal`, ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY `date` DESC) AS rn
        FROM sig WHERE `signal` != 'Hold'
    )
    SELECT stock, version, `date`, `signal` FROM ranked_signals WHERE rn = 1;
    """)
    last_sigs = {(r[0], r[1]): (str(r[2]), r[3]) for r in cur.fetchall()}
    t15_last_ok = (last_sigs.get(("TCS", "adjusted")) == ("2018-04-20", "Buy") and
                   last_sigs.get(("TCS", "raw")) == ("2018-06-05", "Sell") and
                   last_sigs.get(("Infosys", "adjusted")) == ("2018-05-07", "Buy") and
                   last_sigs.get(("Infosys", "raw")) == ("2018-05-07", "Buy"))

    check("T14/T15: TCS/Infosys raw vs adjusted signal counts, differing dates, and last signals",
          t15_counts_ok and t15_diffs_ok and t15_last_ok,
          f"counts_ok={t15_counts_ok}, diffs_ok={t15_diffs_ok}, last_ok={t15_last_ok}")

    # T16: summary as in STEP 2a; signal pairs 30 days or less: Bajaj 11, Eicher 1, Hero 4, Infosys 6, TCS 8, TVS 4 (total 34); 54 round trips, 21 winners
    cur.execute("""
    WITH prices AS (
        SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
        UNION ALL SELECT 'Eicher Motors', `date`, close_price FROM eicher_motors
        UNION ALL SELECT 'Hero Motocorp', `date`, close_price FROM hero_motocorp
        UNION ALL SELECT 'Infosys', `date`, CASE WHEN `date` < '2015-06-15' THEN close_price / 2.0 ELSE close_price END FROM infosys
        UNION ALL SELECT 'TCS', `date`, CASE WHEN `date` < '2018-05-31' THEN close_price / 2.0 ELSE close_price END FROM tcs
        UNION ALL SELECT 'TVS Motors', `date`, close_price FROM tvs_motors
    ),
    ma AS (
        SELECT stock, `date`, close_price,
            CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 20
                 THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma20,
            CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 50
                 THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma50
        FROM prices
    ),
    lagged AS (
        SELECT stock, `date`, close_price, ma20, ma50,
            LAG(ma20) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma20,
            LAG(ma50) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma50
        FROM ma
    ),
    sig AS (
        SELECT stock, `date`, close_price,
            CASE WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
                 WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
                 WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell' ELSE 'Hold' END AS `signal`
        FROM lagged
    ),
    ledger AS (
        SELECT stock, `date`, `signal`, close_price,
            LAG(`date`) OVER (PARTITION BY stock ORDER BY `date`) AS prev_date,
            LAG(`signal`) OVER (PARTITION BY stock ORDER BY `date`) AS prev_signal,
            LAG(close_price) OVER (PARTITION BY stock ORDER BY `date`) AS prev_close,
            DATEDIFF(`date`, LAG(`date`) OVER (PARTITION BY stock ORDER BY `date`)) AS gap_days
        FROM sig WHERE `signal` != 'Hold'
    )
    SELECT stock, COUNT(CASE WHEN gap_days <= 30 THEN 1 END) AS short_pairs
    FROM ledger WHERE prev_date IS NOT NULL GROUP BY stock ORDER BY stock;
    """)
    short_pairs = {r[0]: r[1] for r in cur.fetchall()}
    expected_short_pairs = {"Bajaj Auto": 11, "Eicher Motors": 1, "Hero Motocorp": 4, "Infosys": 6, "TCS": 8, "TVS Motors": 4}
    short_pairs_ok = short_pairs == expected_short_pairs and sum(short_pairs.values()) == 34

    cur.execute("""
    WITH prices AS (
        SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
        UNION ALL SELECT 'Eicher Motors', `date`, close_price FROM eicher_motors
        UNION ALL SELECT 'Hero Motocorp', `date`, close_price FROM hero_motocorp
        UNION ALL SELECT 'Infosys', `date`, CASE WHEN `date` < '2015-06-15' THEN close_price / 2.0 ELSE close_price END FROM infosys
        UNION ALL SELECT 'TCS', `date`, CASE WHEN `date` < '2018-05-31' THEN close_price / 2.0 ELSE close_price END FROM tcs
        UNION ALL SELECT 'TVS Motors', `date`, close_price FROM tvs_motors
    ),
    ma AS (
        SELECT stock, `date`, close_price,
            CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 20
                 THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma20,
            CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 50
                 THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma50
        FROM prices
    ),
    lagged AS (
        SELECT stock, `date`, close_price, ma20, ma50,
            LAG(ma20) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma20,
            LAG(ma50) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma50
        FROM ma
    ),
    sig AS (
        SELECT stock, `date`, close_price,
            CASE WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
                 WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
                 WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell' ELSE 'Hold' END AS `signal`
        FROM lagged
    ),
    ledger AS (
        SELECT stock, `date`, `signal`, close_price,
            LAG(`date`) OVER (PARTITION BY stock ORDER BY `date`) AS prev_date,
            LAG(`signal`) OVER (PARTITION BY stock ORDER BY `date`) AS prev_signal,
            LAG(close_price) OVER (PARTITION BY stock ORDER BY `date`) AS prev_close,
            DATEDIFF(`date`, LAG(`date`) OVER (PARTITION BY stock ORDER BY `date`)) AS gap_days
        FROM sig WHERE `signal` != 'Hold'
    ),
    round_trips AS (
        SELECT stock, prev_date AS buy_date, `date` AS sell_date, prev_close AS buy_close, close_price AS sell_close, gap_days,
            100.0 * (close_price - prev_close) / prev_close AS ret_pct
        FROM ledger WHERE prev_signal = 'Buy' AND `signal` = 'Sell'
    )
    SELECT stock, COUNT(*) AS round_trips, SUM(CASE WHEN ret_pct > 0 THEN 1 ELSE 0 END) AS winners,
        ROUND(AVG(ret_pct), 1) AS avg_return_pct,
        COUNT(CASE WHEN gap_days <= 30 THEN 1 END) AS round_trips_le_30,
        ROUND(AVG(CASE WHEN gap_days <= 30 THEN ret_pct END), 1) AS avg_return_le_30_pct
    FROM round_trips GROUP BY stock ORDER BY stock;
    """)
    t16_rows = cur.fetchall()
    t16_dict = {r[0]: (r[1], r[2], float(r[3]), r[4], float(r[5]) if r[5] is not None else None) for r in t16_rows}
    expected_t16 = {
        "Bajaj Auto": (11, 4, 0.4, 5, -4.1),
        "Eicher Motors": (6, 6, 10.2, 0, None),
        "Hero Motocorp": (9, 3, -1.7, 1, -6.5),
        "Infosys": (9, 3, -0.4, 2, -3.3),
        "TCS": (11, 2, -3.4, 1, -4.4),
        "TVS Motors": (8, 3, 11.2, 2, -8.3),
    }
    t16_summary_ok = True
    for s, exp in expected_t16.items():
        act = t16_dict.get(s)
        if not act:
            t16_summary_ok = False
            break
        if act[0] != exp[0] or act[1] != exp[1] or abs(act[2] - exp[2]) > 0.05 or act[3] != exp[3]:
            t16_summary_ok = False
            break
        if exp[4] is None and act[4] is not None:
            t16_summary_ok = False
            break
        if exp[4] is not None and (act[4] is None or abs(act[4] - exp[4]) > 0.05):
            t16_summary_ok = False
            break

    total_rt = sum(r[1] for r in t16_rows)
    total_winners = sum(r[2] for r in t16_rows)
    t16_ok = short_pairs_ok and t16_summary_ok and total_rt == 54 and total_winners == 21
    check("T16: whipsaws summary, short-gap pairs (34 total), 54 round trips, 21 winners",
          t16_ok, f"summary_ok={t16_summary_ok}, short_pairs_ok={short_pairs_ok}, total_rt={total_rt}, total_winners={total_winners}")

    conn.close()

    print("\n" + "=" * 60)
    if overall_pass:
        print("OVERALL CHECKPOINTS STATUS: ALL PASS")
    else:
        print("OVERALL CHECKPOINTS STATUS: SOME FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
