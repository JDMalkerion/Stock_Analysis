"""
verify_report.py  –  independent check of every claim value in insights.md.
Recomputes from data/stocks.db without reusing make_report.py logic.
Prints PASS/FAIL per check. Also validates image links and text presence.
"""

import os
import re
import sqlite3

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH     = os.path.join(BASE_DIR, "data", "stocks.db")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
IMG_DIR     = os.path.join(REPORTS_DIR, "images")
REPORT_PATH = os.path.join(REPORTS_DIR, "insights.md")

conn   = sqlite3.connect(DB_PATH)
cur    = conn.cursor()

PASS_COUNT = 0
FAIL_COUNT = 0

def check(label, expected, actual, tol=0.0):
    global PASS_COUNT, FAIL_COUNT
    if tol:
        ok = abs(float(actual) - float(expected)) <= tol
    else:
        ok = (actual == expected)
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    print(f"  [{status}] {label}: expected={expected!r}  got={actual!r}")

def sql1(q):
    cur.execute(q)
    return cur.fetchone()[0]

def sql_row(q):
    cur.execute(q)
    return cur.fetchone()

# ── 1. Raw trading days and date range ───────────────────────────────────────
print("\n── 1. Dataset integrity ──")
check("trading days (bajaj_auto)",  889, sql1("SELECT COUNT(*) FROM bajaj_auto"))
check("MIN date (bajaj_auto)",  "2015-01-01", sql1("SELECT MIN(date) FROM bajaj_auto"))
check("MAX date (bajaj_auto)",  "2018-07-31", sql1("SELECT MAX(date) FROM bajaj_auto"))
for tbl in ["eicher_motors","hero_motocorp","infosys","tcs","tvs_motors"]:
    check(f"row count {tbl}", 889, sql1(f"SELECT COUNT(*) FROM {tbl}"))

# ── 2. Adjusted % change ─────────────────────────────────────────────────────
print("\n── 2. Adjusted % change first→last close ──")

ADJ_EVENTS = {"tcs": "2018-05-31", "infosys": "2015-06-15"}

def adj_pct(table, event_date=None):
    if event_date:
        fc_q = f"SELECT CASE WHEN date<'{event_date}' THEN close_price/2.0 ELSE close_price END FROM {table} ORDER BY date ASC LIMIT 1"
        lc_q = f"SELECT CASE WHEN date<'{event_date}' THEN close_price/2.0 ELSE close_price END FROM {table} ORDER BY date DESC LIMIT 1"
    else:
        fc_q = f"SELECT close_price FROM {table} ORDER BY date ASC LIMIT 1"
        lc_q = f"SELECT close_price FROM {table} ORDER BY date DESC LIMIT 1"
    fc = sql1(fc_q)
    lc = sql1(lc_q)
    return round(100.0 * (lc - fc) / fc, 1)

check("TVS Motors adj % change",  86.9, adj_pct("tvs_motors"),  tol=0.05)
check("Eicher Motors adj % change", 82.6, adj_pct("eicher_motors"), tol=0.05)
check("TCS adj % change",  52.4, adj_pct("tcs", "2018-05-31"),  tol=0.05)
check("Infosys adj % change", 38.2, adj_pct("infosys","2015-06-15"), tol=0.05)
check("Bajaj Auto adj % change", 10.0, adj_pct("bajaj_auto"), tol=0.05)
check("Hero Motocorp adj % change", 6.0, adj_pct("hero_motocorp"), tol=0.05)

print("\n── 3. Raw % change (TCS and Infosys) ──")
check("TCS raw % change",    -23.8, adj_pct("tcs"),    tol=0.05)
check("Infosys raw % change", -30.9, adj_pct("infosys"), tol=0.05)

# ── 3. Signal counts (adjusted series) ───────────────────────────────────────
print("\n── 4. Signal counts (adjusted series) ──")

PRICES_CTE = """WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto
    UNION ALL SELECT 'Eicher Motors', date, close_price FROM eicher_motors
    UNION ALL SELECT 'Hero Motocorp', date, close_price FROM hero_motocorp
    UNION ALL SELECT 'Infosys', date, CASE WHEN date<'2015-06-15' THEN close_price/2.0 ELSE close_price END FROM infosys
    UNION ALL SELECT 'TCS', date, CASE WHEN date<'2018-05-31' THEN close_price/2.0 ELSE close_price END FROM tcs
    UNION ALL SELECT 'TVS Motors', date, close_price FROM tvs_motors
),
ma AS (SELECT stock,date,close_price,
    CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date)>=20
         THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma20,
    CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date)>=50
         THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma50
    FROM prices),
lagged AS (SELECT *,LAG(ma20) OVER (PARTITION BY stock ORDER BY date) pm20,LAG(ma50) OVER (PARTITION BY stock ORDER BY date) pm50 FROM ma),
sig AS (SELECT stock,date,close_price,
    CASE WHEN ma20 IS NULL OR ma50 IS NULL OR pm20 IS NULL OR pm50 IS NULL THEN 'Hold'
         WHEN ma20>ma50 AND pm20<=pm50 THEN 'Buy'
         WHEN ma20<ma50 AND pm20>=pm50 THEN 'Sell' ELSE 'Hold' END AS signal FROM lagged)"""

def sig_counts(stock):
    cur.execute(PRICES_CTE + f"""
SELECT SUM(CASE WHEN signal='Buy' THEN 1 ELSE 0 END),
       SUM(CASE WHEN signal='Sell' THEN 1 ELSE 0 END)
FROM sig WHERE stock='{stock}'""")
    return cur.fetchone()

b, s = sig_counts("Bajaj Auto");  check("Bajaj buys",  12, b); check("Bajaj sells",  11, s)
b, s = sig_counts("Eicher Motors"); check("Eicher buys", 6, b); check("Eicher sells", 7, s)
b, s = sig_counts("Hero Motocorp"); check("Hero buys",   9, b); check("Hero sells",   9, s)
b, s = sig_counts("TVS Motors");    check("TVS buys",    8, b); check("TVS sells",    8, s)
b, s = sig_counts("TCS");           check("TCS adj buys",12,b); check("TCS adj sells",12,s)
b, s = sig_counts("Infosys");       check("Infosys adj buys",10,b); check("Infosys adj sells",10,s)

# ── 4. Raw signal counts for TCS and Infosys ─────────────────────────────────
print("\n── 5. Raw signal counts (TCS and Infosys) ──")

def raw_sig_counts(table, stock):
    cur.execute(f"""WITH ma AS (SELECT date,close_price,
    CASE WHEN ROW_NUMBER() OVER (ORDER BY date)>=20
         THEN AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) ELSE NULL END ma20,
    CASE WHEN ROW_NUMBER() OVER (ORDER BY date)>=50
         THEN AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) ELSE NULL END ma50
    FROM {table}),
lagged AS (SELECT *,LAG(ma20) OVER (ORDER BY date) pm20,LAG(ma50) OVER (ORDER BY date) pm50 FROM ma),
sig AS (SELECT CASE WHEN ma20 IS NULL OR ma50 IS NULL OR pm20 IS NULL OR pm50 IS NULL THEN 'Hold'
               WHEN ma20>ma50 AND pm20<=pm50 THEN 'Buy'
               WHEN ma20<ma50 AND pm20>=pm50 THEN 'Sell' ELSE 'Hold' END AS signal FROM lagged)
SELECT SUM(CASE WHEN signal='Buy' THEN 1 ELSE 0 END), SUM(CASE WHEN signal='Sell' THEN 1 ELSE 0 END) FROM sig""")
    return cur.fetchone()

b,s = raw_sig_counts("tcs","TCS");     check("TCS raw buys",  12,b); check("TCS raw sells", 13,s)
b,s = raw_sig_counts("infosys","Inf"); check("Inf raw buys",   9,b); check("Inf raw sells",  9,s)

# ── 5. Last signals ───────────────────────────────────────────────────────────
print("\n── 6. Last non-Hold signals (adjusted) ──")

def last_sig_date(stock):
    cur.execute(PRICES_CTE + f"""
SELECT date FROM sig WHERE stock='{stock}' AND signal!='Hold'
ORDER BY date DESC LIMIT 1""")
    return cur.fetchone()[0]

def last_sig_type(stock):
    cur.execute(PRICES_CTE + f"""
SELECT signal FROM sig WHERE stock='{stock}' AND signal!='Hold'
ORDER BY date DESC LIMIT 1""")
    return cur.fetchone()[0]

check("Bajaj last sig date", "2018-06-21", last_sig_date("Bajaj Auto"))
check("Bajaj last sig type", "Buy",        last_sig_type("Bajaj Auto"))
check("Eicher last sig date","2018-06-06", last_sig_date("Eicher Motors"))
check("Eicher last sig type","Sell",       last_sig_type("Eicher Motors"))
check("Hero last sig date",  "2018-05-22", last_sig_date("Hero Motocorp"))
check("Hero last sig type",  "Sell",       last_sig_type("Hero Motocorp"))
check("TVS last sig date",   "2018-05-17", last_sig_date("TVS Motors"))
check("TVS last sig type",   "Sell",       last_sig_type("TVS Motors"))
check("Infosys adj last sig date","2018-05-07", last_sig_date("Infosys"))
check("Infosys adj last sig type","Buy",        last_sig_type("Infosys"))
check("TCS adj last sig date","2018-04-20",     last_sig_date("TCS"))
check("TCS adj last sig type","Buy",            last_sig_type("TCS"))

# Raw last signal TCS
cur.execute("""WITH ma AS (SELECT date,close_price,
    CASE WHEN ROW_NUMBER() OVER (ORDER BY date)>=20
         THEN AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) ELSE NULL END ma20,
    CASE WHEN ROW_NUMBER() OVER (ORDER BY date)>=50
         THEN AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) ELSE NULL END ma50 FROM tcs),
lagged AS (SELECT *,LAG(ma20) OVER (ORDER BY date) pm20,LAG(ma50) OVER (ORDER BY date) pm50 FROM ma),
sig AS (SELECT date, CASE WHEN ma20 IS NULL OR ma50 IS NULL OR pm20 IS NULL OR pm50 IS NULL THEN 'Hold'
               WHEN ma20>ma50 AND pm20<=pm50 THEN 'Buy'
               WHEN ma20<ma50 AND pm20>=pm50 THEN 'Sell' ELSE 'Hold' END signal FROM lagged)
SELECT date, signal FROM sig WHERE signal!='Hold' ORDER BY date DESC LIMIT 1""")
r = cur.fetchone()
check("TCS raw last sig date", "2018-06-05", r[0])
check("TCS raw last sig type", "Sell",       r[1])

# ── 6. Signal differences raw vs adjusted ────────────────────────────────────
print("\n── 7. Raw vs adjusted signal differences ──")
cur.execute("""
WITH both AS (
    SELECT 'TCS' AS stock,'raw' AS ver,date,close_price FROM tcs
    UNION ALL SELECT 'TCS','adjusted',date,CASE WHEN date<'2018-05-31' THEN close_price/2.0 ELSE close_price END FROM tcs
    UNION ALL SELECT 'Infosys','raw',date,close_price FROM infosys
    UNION ALL SELECT 'Infosys','adjusted',date,CASE WHEN date<'2015-06-15' THEN close_price/2.0 ELSE close_price END FROM infosys
),
ma AS (SELECT stock,ver,date,close_price,
    CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock,ver ORDER BY date)>=20
         THEN ROUND(AVG(close_price) OVER (PARTITION BY stock,ver ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW),2) ELSE NULL END ma20,
    CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock,ver ORDER BY date)>=50
         THEN ROUND(AVG(close_price) OVER (PARTITION BY stock,ver ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW),2) ELSE NULL END ma50 FROM both),
lagged AS (SELECT *,LAG(ma20) OVER (PARTITION BY stock,ver ORDER BY date) pm20,LAG(ma50) OVER (PARTITION BY stock,ver ORDER BY date) pm50 FROM ma),
sig AS (SELECT stock,ver,date,CASE WHEN ma20 IS NULL OR ma50 IS NULL OR pm20 IS NULL OR pm50 IS NULL THEN 'Hold'
               WHEN ma20>ma50 AND pm20<=pm50 THEN 'Buy'
               WHEN ma20<ma50 AND pm20>=pm50 THEN 'Sell' ELSE 'Hold' END signal FROM lagged)
SELECT r.stock,r.date FROM (SELECT stock,date,signal FROM sig WHERE ver='raw') r
JOIN (SELECT stock,date,signal FROM sig WHERE ver='adjusted') a ON r.stock=a.stock AND r.date=a.date
WHERE r.signal!=a.signal ORDER BY r.stock,r.date""")
diff_dates = [(r[0], r[1]) for r in cur.fetchall()]
expected_diffs = [
    ("Infosys", "2015-07-01"), ("Infosys","2015-07-08"),
    ("Infosys","2015-07-27"),  ("Infosys","2015-08-18"),
    ("TCS","2018-06-05"),
]
check("raw vs adj diff count", 5, len(diff_dates))
for (es, ed) in expected_diffs:
    check(f"diff {es} {ed}", True, (es, ed) in diff_dates)

# ── 7. Round trips ────────────────────────────────────────────────────────────
print("\n── 8. Round-trip counts and summary ──")

cur.execute(PRICES_CTE + """,
ledger AS (SELECT stock,date,signal,close_price,
    LAG(date) OVER (PARTITION BY stock ORDER BY date) pd,
    LAG(signal) OVER (PARTITION BY stock ORDER BY date) ps,
    LAG(close_price) OVER (PARTITION BY stock ORDER BY date) pc,
    CAST(ROUND(julianday(date)-julianday(LAG(date) OVER (PARTITION BY stock ORDER BY date))) AS INTEGER) gap
    FROM sig WHERE signal!='Hold')
SELECT stock,COUNT(*),SUM(CASE WHEN (close_price-pc)/pc>0 THEN 1 ELSE 0 END),
    ROUND(AVG(100.0*(close_price-pc)/pc),1),
    COUNT(CASE WHEN gap<=30 THEN 1 END),
    ROUND(AVG(CASE WHEN gap<=30 THEN 100.0*(close_price-pc)/pc END),1)
FROM ledger WHERE ps='Buy' AND signal='Sell' GROUP BY stock ORDER BY stock""")
rt_rows = cur.fetchall()
rt_map = {r[0]: r for r in rt_rows}

expected_rt = {
    "Bajaj Auto":    (11, 4,  0.4, 5, -4.1),
    "Eicher Motors": (6,  6, 10.1, 0, None),
    "Hero Motocorp": (9,  3, -1.7, 1, -6.5),
    "Infosys":       (9,  3, -0.4, 2, -3.3),
    "TCS":           (11, 2, -3.4, 1, -4.4),
    "TVS Motors":    (8,  3, 11.2, 2, -8.3),
}
for s, (trips, winners, avg_ret, short, avg_short) in expected_rt.items():
    r = rt_map.get(s)
    if r is None:
        check(f"{s} round trips", trips, None)
        continue
    check(f"{s} round trips",    trips,   r[1])
    check(f"{s} winners",        winners, r[2])
    check(f"{s} avg return",     avg_ret, r[3], tol=0.15)
    check(f"{s} short trips",    short,   r[4])
    if avg_short is None:
        check(f"{s} avg short return", None, r[5])
    else:
        check(f"{s} avg short return", avg_short, r[5], tol=0.05)

total_rt = sum(r[1] for r in rt_rows)
total_winners = sum(r[2] for r in rt_rows)
check("total round trips", 54, total_rt)
check("total winners",     21, total_winners)

# ── 8. Consecutive-signal pairs <= 30 days ────────────────────────────────────
print("\n── 9. Consecutive-signal pairs ≤ 30 days ──")
cur.execute(PRICES_CTE + """,
ledger AS (SELECT stock,
    CAST(ROUND(julianday(date)-julianday(LAG(date) OVER (PARTITION BY stock ORDER BY date))) AS INTEGER) gap
    FROM sig WHERE signal!='Hold')
SELECT stock,COUNT(CASE WHEN gap<=30 THEN 1 END) FROM ledger
WHERE gap IS NOT NULL GROUP BY stock ORDER BY stock""")
sp_rows = {r[0]: r[1] for r in cur.fetchall()}

expected_sp = {"Bajaj Auto":11,"Eicher Motors":1,"Hero Motocorp":4,
               "Infosys":6,"TCS":8,"TVS Motors":4}
for s, exp in expected_sp.items():
    check(f"{s} short-gap pairs", exp, sp_rows.get(s))
check("total short-gap pairs", 34, sum(sp_rows.values()))

# ── 9. Short round trips lost money ──────────────────────────────────────────
print("\n── 10. Short round trips that lost money ──")
cur.execute(PRICES_CTE + """,
ledger AS (SELECT stock,date,signal,close_price,
    LAG(date) OVER (PARTITION BY stock ORDER BY date) pd,
    LAG(signal) OVER (PARTITION BY stock ORDER BY date) ps,
    LAG(close_price) OVER (PARTITION BY stock ORDER BY date) pc,
    CAST(ROUND(julianday(date)-julianday(LAG(date) OVER (PARTITION BY stock ORDER BY date))) AS INTEGER) gap
    FROM sig WHERE signal!='Hold')
SELECT COUNT(*) FROM ledger WHERE ps='Buy' AND signal='Sell' AND gap<=30 AND close_price<pc""")
short_losers = cur.fetchone()[0]
check("short RT losers (<=30 days)", 10, short_losers)

total_short_rt = sum(r[4] for r in rt_rows)
check("total short round trips", 11, total_short_rt)

# ── 10. TVS outlier ───────────────────────────────────────────────────────────
print("\n── 11. TVS outlier trade ──")
cur.execute(PRICES_CTE + """,
ledger AS (SELECT stock,date,signal,close_price,
    LAG(date) OVER (PARTITION BY stock ORDER BY date) pd,
    LAG(signal) OVER (PARTITION BY stock ORDER BY date) ps,
    LAG(close_price) OVER (PARTITION BY stock ORDER BY date) pc
    FROM sig WHERE signal!='Hold')
SELECT pd,date,ROUND(100.0*(close_price-pc)/pc,1) FROM ledger
WHERE stock='TVS Motors' AND ps='Buy' AND signal='Sell' AND pd='2017-01-06'""")
tvs_row = cur.fetchone()
check("TVS outlier buy date",  "2017-01-06", tvs_row[0] if tvs_row else None)
check("TVS outlier sell date", "2018-01-29", tvs_row[1] if tvs_row else None)
check("TVS outlier return",    86.7,          tvs_row[2] if tvs_row else None, tol=0.05)

# ── 11. Image links in report ─────────────────────────────────────────────────
print("\n── 12. Image link validation ──")
with open(REPORT_PATH, "r", encoding="utf-8") as f:
    md = f.read()

image_links = re.findall(r'!\[.*?\]\((images/[^)]+)\)', md)
for link in image_links:
    full_path = os.path.join(REPORTS_DIR, link)
    exists = os.path.isfile(full_path)
    check(f"image exists: {link}", True, exists)

# ── 12. Key numbers present in report text ────────────────────────────────────
print("\n── 13. Key numbers present in report text ──")

def text_contains(pattern):
    return bool(re.search(pattern, md))

check("report contains TVS 86.9%",           True, text_contains(r"86\.9"))
check("report contains Eicher 82.6%",        True, text_contains(r"82\.6"))
check("report contains TCS adj 52.4%",       True, text_contains(r"52\.4"))
check("report contains Infosys adj 38.2%",   True, text_contains(r"38\.2"))
check("report contains Bajaj 10.0%",         True, text_contains(r"10\.0"))
check("report contains Hero 6.0%",           True, text_contains(r"6\.0"))
check("report contains TCS raw -23.8%",      True, text_contains(r"-23\.8"))
check("report contains Infosys raw -30.9%",  True, text_contains(r"-30\.9"))
check("report contains Bajaj 12 buys",       True, text_contains(r"12\s*\|\s*11"))
check("report contains TCS adj 12/12",       True, text_contains(r"12\s*\|\s*12"))
check("report contains 2018-06-21",          True, text_contains(r"2018-06-21"))
check("report contains 54 round trips",      True, text_contains(r"54"))
check("report contains 21 winners",          True, text_contains(r"21"))
check("report contains 34 short pairs",      True, text_contains(r"34"))
check("report contains 11 short round trips",  True, text_contains(r"\b11\b"))

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"Results: {PASS_COUNT} PASS  |  {FAIL_COUNT} FAIL")
print(f"{'='*50}")

conn.close()
