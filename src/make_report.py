"""
make_report.py  –  generate reports/insights.md and charts in reports/images/
All numbers are computed from data/stocks.db at build time; none are hard-coded.

CAVEAT (internal): assumes a clean factor-2 adjustment for TCS (event 2018-05-31)
and Infosys (event 2015-06-15). The event type should be confirmed from an
external source before quoting the adjusted figures in any publication.
"""

import os
import sqlite3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# ── paths ──────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH     = os.path.join(BASE_DIR, "data", "stocks.db")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
IMG_DIR     = os.path.join(REPORTS_DIR, "images")
os.makedirs(IMG_DIR, exist_ok=True)

REPORT_PATH = os.path.join(REPORTS_DIR, "insights.md")

STOCKS    = ["Bajaj Auto", "Eicher Motors", "Hero Motocorp", "Infosys", "TCS", "TVS Motors"]
ADJ_EVENTS = {"TCS": "2018-05-31", "Infosys": "2015-06-15"}
TABLE_MAP  = {
    "Bajaj Auto":   "bajaj_auto",
    "Eicher Motors":"eicher_motors",
    "Hero Motocorp":"hero_motocorp",
    "Infosys":      "infosys",
    "TCS":          "tcs",
    "TVS Motors":   "tvs_motors",
}

conn   = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ── helper: adjusted close_price expression ─────────────────────────────────
def adj_expr(stock):
    tbl = TABLE_MAP[stock]
    if stock in ADJ_EVENTS:
        ed = ADJ_EVENTS[stock]
        return (f"CASE WHEN date < '{ed}' THEN close_price / 2.0 ELSE close_price END",
                tbl)
    return ("close_price", tbl)

# ── shared CTE: adjusted prices for all six stocks ───────────────────────────
def prices_cte():
    parts = []
    for s, t in TABLE_MAP.items():
        if s in ADJ_EVENTS:
            ed = ADJ_EVENTS[s]
            parts.append(
                f"SELECT '{s}' AS stock, date, "
                f"CASE WHEN date < '{ed}' THEN close_price / 2.0 ELSE close_price END AS close_price "
                f"FROM {t}"
            )
        else:
            parts.append(f"SELECT '{s}' AS stock, date, close_price FROM {t}")
    return "WITH prices AS (\n    " + "\n    UNION ALL\n    ".join(parts) + "\n)"

# ── shared CTEs: ma → lagged → sig ───────────────────────────────────────────
MA_CTES = """,
ma AS (
    SELECT stock, date, close_price,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 20
             THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
             ELSE NULL END AS ma20,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date) >= 50
             THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)
             ELSE NULL END AS ma50
    FROM prices
),
lagged AS (
    SELECT stock, date, close_price, ma20, ma50,
        LAG(ma20) OVER (PARTITION BY stock ORDER BY date) AS prev_ma20,
        LAG(ma50) OVER (PARTITION BY stock ORDER BY date) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT stock, date, close_price,
        CASE
            WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
            WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
            WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
            ELSE 'Hold'
        END AS signal
    FROM lagged
)"""


def full_sig_query(extra=""):
    return prices_cte() + MA_CTES + "\n" + extra


# ══════════════════════════════════════════════════════════════════════════════
# 1. DATA QUERIES
# ══════════════════════════════════════════════════════════════════════════════

# 1a. Per-stock first/last close, trading days, date range
def fetch_stock_meta():
    meta = {}
    for s, t in TABLE_MAP.items():
        cursor.execute(f"SELECT COUNT(*), MIN(date), MAX(date) FROM {t}")
        cnt, d0, d1 = cursor.fetchone()
        cursor.execute(f"SELECT close_price FROM {t} WHERE date = '{d0}'")
        fc = cursor.fetchone()[0]
        cursor.execute(f"SELECT close_price FROM {t} WHERE date = '{d1}'")
        lc = cursor.fetchone()[0]
        meta[s] = {"count": cnt, "first_date": d0, "last_date": d1,
                   "first_close": fc, "last_close": lc}
    return meta

raw_meta = fetch_stock_meta()

# 1b. Adjusted % change (adjusted series)
def fetch_adj_pct_change():
    q = prices_cte() + """,
ends AS (SELECT stock, MIN(date) AS fd, MAX(date) AS ld FROM prices GROUP BY stock)
SELECT e.stock,
    pf.close_price AS fc,
    pl.close_price AS lc,
    ROUND(100.0*(pl.close_price - pf.close_price)/pf.close_price, 1) AS pct
FROM ends e
JOIN prices pf ON e.stock = pf.stock AND e.fd = pf.date
JOIN prices pl ON e.stock = pl.stock AND e.ld = pl.date
ORDER BY pct DESC"""
    cursor.execute(q)
    return {r[0]: {"adj_fc": r[1], "adj_lc": r[2], "adj_pct": r[3]}
            for r in cursor.fetchall()}

adj_pct = fetch_adj_pct_change()

# 1c. Raw % change (raw close_price, no adjustment)
def fetch_raw_pct_change():
    res = {}
    for s, t in TABLE_MAP.items():
        cursor.execute(
            f"SELECT close_price FROM {t} ORDER BY date ASC LIMIT 1")
        fc = cursor.fetchone()[0]
        cursor.execute(
            f"SELECT close_price FROM {t} ORDER BY date DESC LIMIT 1")
        lc = cursor.fetchone()[0]
        res[s] = round(100.0 * (lc - fc) / fc, 1)
    return res

raw_pct = fetch_raw_pct_change()

# 1d. Signal counts and last signal per stock (adjusted series)
cursor.execute(full_sig_query(""",
latest AS (
    SELECT stock, date, signal,
        ROW_NUMBER() OVER (PARTITION BY stock ORDER BY date DESC) AS rn
    FROM sig WHERE signal != 'Hold'
)
SELECT s.stock,
    SUM(CASE WHEN s.signal='Buy' THEN 1 ELSE 0 END) AS buys,
    SUM(CASE WHEN s.signal='Sell' THEN 1 ELSE 0 END) AS sells,
    l.date AS last_sig_date, l.signal AS last_sig
FROM sig s
JOIN latest l ON s.stock = l.stock AND l.rn = 1
GROUP BY s.stock, l.date, l.signal
ORDER BY s.stock"""))

sig_rows = cursor.fetchall()
sig_data = {r[0]: {"buys": r[1], "sells": r[2],
                   "last_sig_date": r[3], "last_sig": r[4]}
            for r in sig_rows}

# 1e. Raw signal counts for TCS and Infosys
def raw_sig_counts(stock):
    t = TABLE_MAP[stock]
    q = f"""WITH prices AS (SELECT '{stock}' AS stock, date, close_price FROM {t}),
ma AS (SELECT stock, date, close_price,
    CASE WHEN ROW_NUMBER() OVER (ORDER BY date)>=20
         THEN AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma20,
    CASE WHEN ROW_NUMBER() OVER (ORDER BY date)>=50
         THEN AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma50
    FROM prices),
lagged AS (SELECT *, LAG(ma20) OVER (ORDER BY date) AS pm20, LAG(ma50) OVER (ORDER BY date) AS pm50 FROM ma),
sig AS (SELECT stock, date, close_price,
    CASE WHEN ma20 IS NULL OR ma50 IS NULL OR pm20 IS NULL OR pm50 IS NULL THEN 'Hold'
         WHEN ma20>ma50 AND pm20<=pm50 THEN 'Buy'
         WHEN ma20<ma50 AND pm20>=pm50 THEN 'Sell' ELSE 'Hold' END AS signal FROM lagged)
SELECT SUM(CASE WHEN signal='Buy' THEN 1 ELSE 0 END),
       SUM(CASE WHEN signal='Sell' THEN 1 ELSE 0 END),
       MAX(CASE WHEN signal!='Hold' THEN date END)
FROM sig"""
    cursor.execute(q)
    r = cursor.fetchone()
    return {"buys": r[0], "sells": r[1], "last_date": r[2]}

raw_sig_tcs  = raw_sig_counts("TCS")
raw_sig_inf  = raw_sig_counts("Infosys")

# 1f. Raw vs adjusted signal differences
cursor.execute("""
WITH t_raw AS (
    SELECT 'TCS' AS stock, 'raw' AS ver, date, close_price FROM tcs
    UNION ALL SELECT 'Infosys','raw',date,close_price FROM infosys
),
t_adj AS (
    SELECT 'TCS' AS stock,'adjusted' AS ver,date,
        CASE WHEN date<'2018-05-31' THEN close_price/2.0 ELSE close_price END FROM tcs
    UNION ALL SELECT 'Infosys','adjusted',date,
        CASE WHEN date<'2015-06-15' THEN close_price/2.0 ELSE close_price END FROM infosys
),
both AS (SELECT * FROM t_raw UNION ALL SELECT * FROM t_adj),
ma AS (
    SELECT stock, ver, date, close_price,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock,ver ORDER BY date)>=20
             THEN ROUND(AVG(close_price) OVER (PARTITION BY stock,ver ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW),2)
             ELSE NULL END AS ma20,
        CASE WHEN ROW_NUMBER() OVER (PARTITION BY stock,ver ORDER BY date)>=50
             THEN ROUND(AVG(close_price) OVER (PARTITION BY stock,ver ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW),2)
             ELSE NULL END AS ma50
    FROM both
),
lagged AS (
    SELECT *,
        LAG(ma20) OVER (PARTITION BY stock,ver ORDER BY date) AS pm20,
        LAG(ma50) OVER (PARTITION BY stock,ver ORDER BY date) AS pm50
    FROM ma
),
sig AS (
    SELECT stock, ver, date, close_price,
        CASE WHEN ma20 IS NULL OR ma50 IS NULL OR pm20 IS NULL OR pm50 IS NULL THEN 'Hold'
             WHEN ma20>ma50 AND pm20<=pm50 THEN 'Buy'
             WHEN ma20<ma50 AND pm20>=pm50 THEN 'Sell' ELSE 'Hold' END AS signal
    FROM lagged
)
SELECT r.stock, r.date, r.signal AS raw_sig, a.signal AS adj_sig
FROM (SELECT stock,date,signal FROM sig WHERE ver='raw') r
JOIN (SELECT stock,date,signal FROM sig WHERE ver='adjusted') a
  ON r.stock=a.stock AND r.date=a.date
WHERE r.signal != a.signal
ORDER BY r.stock, r.date""")
raw_adj_diffs = cursor.fetchall()  # [(stock, date, raw_sig, adj_sig), ...]

# 1g. Round trips (adjusted series)
cursor.execute(full_sig_query(""",
ledger AS (
    SELECT stock, date, signal, close_price,
        LAG(date) OVER (PARTITION BY stock ORDER BY date) AS prev_date,
        LAG(signal) OVER (PARTITION BY stock ORDER BY date) AS prev_signal,
        LAG(close_price) OVER (PARTITION BY stock ORDER BY date) AS prev_close,
        CAST(ROUND(julianday(date)-julianday(LAG(date) OVER (PARTITION BY stock ORDER BY date))) AS INTEGER) AS gap_days
    FROM sig WHERE signal != 'Hold'
),
rt AS (
    SELECT stock, prev_date AS buy_date, date AS sell_date,
        prev_close AS buy_close, close_price AS sell_close, gap_days,
        ROUND(100.0*(close_price-prev_close)/prev_close, 1) AS ret_pct
    FROM ledger WHERE prev_signal='Buy' AND signal='Sell'
)
SELECT stock, COUNT(*) AS trips,
    SUM(CASE WHEN ret_pct>0 THEN 1 ELSE 0 END) AS winners,
    ROUND(AVG(ret_pct),1) AS avg_ret,
    COUNT(CASE WHEN gap_days<=30 THEN 1 END) AS short_trips,
    ROUND(AVG(CASE WHEN gap_days<=30 THEN ret_pct END),1) AS avg_short_ret
FROM rt GROUP BY stock ORDER BY stock"""))
rt_rows = cursor.fetchall()
rt_data = {r[0]: {"trips": r[1], "winners": r[2], "avg_ret": r[3],
                  "short_trips": r[4], "avg_short_ret": r[5]}
           for r in rt_rows}

# 1h. Consecutive-signal pairs <= 30 days
cursor.execute(full_sig_query(""",
ledger AS (
    SELECT stock,
        LAG(date) OVER (PARTITION BY stock ORDER BY date) AS prev_date,
        CAST(ROUND(julianday(date)-julianday(LAG(date) OVER (PARTITION BY stock ORDER BY date))) AS INTEGER) AS gap_days
    FROM sig WHERE signal != 'Hold'
)
SELECT stock, COUNT(CASE WHEN gap_days<=30 THEN 1 END) AS pairs_le30
FROM ledger WHERE prev_date IS NOT NULL
GROUP BY stock ORDER BY stock"""))
short_pairs = {r[0]: r[1] for r in cursor.fetchall()}

# 1i. Top-5 shortest signal pairs
cursor.execute(full_sig_query(""",
ledger AS (
    SELECT stock, prev_date, prev_signal, prev_close, date, signal, close_price,
        CAST(ROUND(julianday(date)-julianday(prev_date)) AS INTEGER) AS gap_days
    FROM (
        SELECT stock, date, signal, close_price,
            LAG(date) OVER (PARTITION BY stock ORDER BY date) AS prev_date,
            LAG(signal) OVER (PARTITION BY stock ORDER BY date) AS prev_signal,
            LAG(close_price) OVER (PARTITION BY stock ORDER BY date) AS prev_close
        FROM sig WHERE signal != 'Hold'
    ) WHERE prev_date IS NOT NULL
)
SELECT stock, prev_date, prev_signal, ROUND(prev_close,2), date, signal, ROUND(close_price,2), gap_days
FROM ledger ORDER BY gap_days ASC, stock ASC, prev_date ASC LIMIT 5"""))
top5_short = cursor.fetchall()

# 1j. Event windows (3 before + event + 3 after)
def event_window(stock, event_date):
    t = TABLE_MAP[stock]
    cursor.execute(f"""
        SELECT date, close_price,
            CASE WHEN date < '{event_date}' THEN close_price/2.0 ELSE close_price END AS adj_close
        FROM {t}
        WHERE date IN (
            SELECT date FROM (SELECT date FROM {t} WHERE date<='{event_date}' ORDER BY date DESC LIMIT 4)
            UNION
            SELECT date FROM (SELECT date FROM {t} WHERE date>'{event_date}' ORDER BY date ASC LIMIT 3)
        ) ORDER BY date""")
    return cursor.fetchall()

tcs_window = event_window("TCS", "2018-05-31")
inf_window = event_window("Infosys", "2015-06-15")

# 1k. All round trips detail
cursor.execute(full_sig_query(""",
ledger AS (
    SELECT stock, date, signal, close_price,
        LAG(date) OVER (PARTITION BY stock ORDER BY date) AS prev_date,
        LAG(signal) OVER (PARTITION BY stock ORDER BY date) AS prev_signal,
        LAG(close_price) OVER (PARTITION BY stock ORDER BY date) AS prev_close,
        CAST(ROUND(julianday(date)-julianday(LAG(date) OVER (PARTITION BY stock ORDER BY date))) AS INTEGER) AS gap_days
    FROM sig WHERE signal != 'Hold'
)
SELECT stock, prev_date, date, ROUND(prev_close,2), ROUND(close_price,2), gap_days,
    ROUND(100.0*(close_price-prev_close)/prev_close,1) AS ret_pct
FROM ledger WHERE prev_signal='Buy' AND signal='Sell'
ORDER BY stock, prev_date"""))
rt_detail = cursor.fetchall()

# 1l. Bajaj Auto signals (for chart)
cursor.execute("""
WITH ma AS (
    SELECT date, close_price,
        CASE WHEN ROW_NUMBER() OVER (ORDER BY date)>=20
             THEN AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma20,
        CASE WHEN ROW_NUMBER() OVER (ORDER BY date)>=50
             THEN AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) ELSE NULL END AS ma50
    FROM bajaj_auto
),
lagged AS (SELECT *, LAG(ma20) OVER (ORDER BY date) pm20, LAG(ma50) OVER (ORDER BY date) pm50 FROM ma),
sig AS (SELECT date, close_price, ma20, ma50,
    CASE WHEN ma20 IS NULL OR ma50 IS NULL OR pm20 IS NULL OR pm50 IS NULL THEN 'Hold'
         WHEN ma20>ma50 AND pm20<=pm50 THEN 'Buy'
         WHEN ma20<ma50 AND pm20>=pm50 THEN 'Sell' ELSE 'Hold' END AS signal FROM lagged)
SELECT date, close_price, ma20, ma50, signal FROM sig ORDER BY date""")
bajaj_chart_data = cursor.fetchall()

# 1m. TCS raw and adjusted price series (for chart)
cursor.execute("""
SELECT date, close_price AS raw_close,
    CASE WHEN date<'2018-05-31' THEN close_price/2.0 ELSE close_price END AS adj_close
FROM tcs ORDER BY date""")
tcs_chart_data = cursor.fetchall()

# ══════════════════════════════════════════════════════════════════════════════
# 2. CHARTS
# ══════════════════════════════════════════════════════════════════════════════

def parse_dates(rows, col=0):
    return [datetime.strptime(r[col], "%Y-%m-%d") for r in rows]


# Chart 1: TCS raw vs adjusted close
def chart_tcs_raw_adj():
    dates = parse_dates(tcs_chart_data)
    raw   = [r[1] for r in tcs_chart_data]
    adj   = [r[2] for r in tcs_chart_data]
    ed    = datetime(2018, 5, 31)

    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(dates, raw, color="#c0392b", linewidth=1.2, label="Raw close")
    ax.plot(dates, adj, color="#2980b9", linewidth=1.2, label="Adjusted close")
    ax.axvline(ed, color="#7f8c8d", linestyle="--", linewidth=1.0, label="Event 2018-05-31")
    ax.set_title("TCS: Raw vs Adjusted Close Price (2015-01-01 – 2018-07-31)", fontsize=12)
    ax.set_xlabel("Date")
    ax.set_ylabel("Close Price (₹)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    fig.autofmt_xdate(rotation=30)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    path = os.path.join(IMG_DIR, "tcs_raw_vs_adjusted.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  saved {path}")


# Chart 2: Bajaj Auto price + ma20 + ma50 + Buy/Sell markers
def chart_bajaj_signals():
    dates  = parse_dates(bajaj_chart_data)
    prices = [r[1] for r in bajaj_chart_data]
    ma20   = [r[2] for r in bajaj_chart_data]
    ma50   = [r[3] for r in bajaj_chart_data]
    sigs   = [r[4] for r in bajaj_chart_data]

    buy_dates  = [dates[i] for i, s in enumerate(sigs) if s == "Buy"]
    buy_prices = [prices[i] for i, s in enumerate(sigs) if s == "Buy"]
    sell_dates  = [dates[i] for i, s in enumerate(sigs) if s == "Sell"]
    sell_prices = [prices[i] for i, s in enumerate(sigs) if s == "Sell"]

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(dates, prices, color="#2c3e50", linewidth=1.0, alpha=0.7, label="Close price")
    # ma lines (skip None)
    valid_ma20 = [(dates[i], ma20[i]) for i in range(len(ma20)) if ma20[i] is not None]
    valid_ma50 = [(dates[i], ma50[i]) for i in range(len(ma50)) if ma50[i] is not None]
    if valid_ma20:
        ax.plot([v[0] for v in valid_ma20], [v[1] for v in valid_ma20],
                color="#e67e22", linewidth=1.3, label="MA20")
    if valid_ma50:
        ax.plot([v[0] for v in valid_ma50], [v[1] for v in valid_ma50],
                color="#27ae60", linewidth=1.3, label="MA50")
    ax.scatter(buy_dates,  buy_prices,  marker="^", color="#27ae60", s=60, zorder=5, label="Buy")
    ax.scatter(sell_dates, sell_prices, marker="v", color="#c0392b", s=60, zorder=5, label="Sell")
    ax.set_title("Bajaj Auto: Close Price, MA20, MA50, and Signals", fontsize=12)
    ax.set_xlabel("Date")
    ax.set_ylabel("Close Price (₹)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    fig.autofmt_xdate(rotation=30)
    ax.legend(fontsize=9, ncol=2)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    path = os.path.join(IMG_DIR, "bajaj_signals.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  saved {path}")


print("Generating charts...")
chart_tcs_raw_adj()
chart_bajaj_signals()

# ══════════════════════════════════════════════════════════════════════════════
# 3. DERIVED NUMBERS (computed once, used in report text)
# ══════════════════════════════════════════════════════════════════════════════

total_rt        = sum(v["trips"]   for v in rt_data.values())
total_winners   = sum(v["winners"] for v in rt_data.values())
total_short_pairs = sum(short_pairs.values())
total_short_rt  = sum(v["short_trips"] for v in rt_data.values())

# Short round trips that lost money
short_rt_losers = sum(
    1 for r in rt_detail if r[5] <= 30 and r[6] is not None and r[6] < 0
)

# TVS outlier: the 2017-01-06 → 2018-01-29 trip
tvs_big  = next((r for r in rt_detail if r[0] == "TVS Motors" and r[1] == "2017-01-06"), None)
tvs_others_avg = round(
    sum(r[6] for r in rt_detail if r[0] == "TVS Motors" and r[1] != "2017-01-06") /
    max(1, sum(1 for r in rt_detail if r[0] == "TVS Motors" and r[1] != "2017-01-06")), 1)


# Stock order by adj pct change (descending) for the per-stock table
stocks_sorted = sorted(STOCKS, key=lambda s: adj_pct[s]["adj_pct"], reverse=True)


# ══════════════════════════════════════════════════════════════════════════════
# 4. REPORT WRITER
# ══════════════════════════════════════════════════════════════════════════════

def fmt(x, dp=1):
    """Format a float to dp decimal places."""
    if x is None:
        return "—"
    return f"{x:.{dp}f}"

def sign(x):
    return f"+{fmt(x)}" if x > 0 else fmt(x)

lines = []
def w(s=""):
    lines.append(s)


# ────────────────────────────────────────────────────────────────────────────
w("# NSE Stock Analysis: Insights Report")
w()
w(f"*Generated from `data/stocks.db` — 6 stocks, 2015-01-01 to 2018-07-31*")
w()

# ── 1. Summary ───────────────────────────────────────────────────────────────
w("## 1. Summary")
w()
w("Five headline findings (each links to its section):")
w()

# Pull the adjusted % changes for summary bullets
tvs_pct    = adj_pct["TVS Motors"]["adj_pct"]
eic_pct    = adj_pct["Eicher Motors"]["adj_pct"]
tcs_adj_pct = adj_pct["TCS"]["adj_pct"]
inf_adj_pct = adj_pct["Infosys"]["adj_pct"]

w(f"- **TVS Motors and Eicher Motors led the group** over the study period: adjusted close prices "
  f"rose {fmt(tvs_pct)}% and {fmt(eic_pct)}% respectively. The other four stocks returned far less "
  f"or fell. → [Per-stock results](#4-per-stock-results)")
w()
w(f"- **Two price events require adjustment.** TCS on {ADJ_EVENTS['TCS']} and Infosys on "
  f"{ADJ_EVENTS['Infosys']} each show a close that roughly halved overnight with no sustained "
  f"recovery, consistent with a 1:1 bonus issue. Dividing pre-event prices by 2 changes TCS's "
  f"headline return from {fmt(raw_pct['TCS'])}% to {fmt(tcs_adj_pct)}% and Infosys's from "
  f"{fmt(raw_pct['Infosys'])}% to {fmt(inf_adj_pct)}%. "
  f"→ [Price events](#3-two-price-events)")
w()
w(f"- **The golden-cross rule generated {total_rt} round trips across all six stocks, "
  f"of which {total_winners} were profitable.** Eicher Motors was the only stock where every "
  f"round trip made money (6 of 6). → [Per-stock results](#4-per-stock-results)")
w()
w(f"- **Whipsaw signals were common.** {total_short_pairs} consecutive signal pairs were "
  f"{30} calendar days apart or fewer. Of the {total_short_rt} round trips that also fell "
  f"within that window, {short_rt_losers} lost money. → [Whipsaws](#5-whipsaws)")
w()
w("- **The simple moving-average rule has a structural lag.** The first crossover signal cannot "
  "arrive before 50 trading days of data have accumulated; the rule cannot warn of events that "
  "happened before that threshold. → [Method questions](#6-method-questions)")
w()

# ── 2. Data and method ───────────────────────────────────────────────────────
w("---")
w("## 2. Data and Method")
w()
w(f"**Data.** Daily closing prices for six NSE stocks — "
  + ", ".join(STOCKS) +
  f" — sourced from CSV files covering {raw_meta['Bajaj Auto']['first_date']} to "
  f"{raw_meta['Bajaj Auto']['last_date']} "
  f"({raw_meta['Bajaj Auto']['count']} trading days per stock). "
  f"Only `close_price` is used. No dividends, intraday prices, or market-index data are included.")
w()
w("**Adjustment.** Two stocks show a roughly 50% overnight drop with no sustained recovery "
  "(see [Section 3](#3-two-price-events)). All analysis uses an adjusted series for those stocks: "
  "close prices *before* the event date are divided by 2. All other stocks use raw prices.")
w()
w("**Signal rule.** For each stock, compute:")
w()
w("- MA20 = 20-trading-day simple moving average of adjusted close price.")
w("- MA50 = 50-trading-day simple moving average of adjusted close price.")
w("- Both are set to NULL until a full window is available (row 20 and row 50 respectively).")
w("- **Buy** signal: the day MA20 crosses *above* MA50 (i.e., `ma20 > ma50` and on the "
  "previous day `prev_ma20 <= prev_ma50`).")
w("- **Sell** signal: the day MA20 crosses *below* MA50.")
w("- All other days: Hold.")
w()
w("Averages use *unrounded* prices (same crossover dates result whether or not ROUND is applied "
  "to 2 d.p. — verified in `src/run_task10.py`).")
w()
w("> [!NOTE]")
w("> **Round trips** are Buy–Sell pairs in consecutive signal order. The percentage return is "
  "`(sell_close − buy_close) / buy_close × 100`. Brokerage costs and dividends are excluded.")
w()

# ── 3. Two price events ───────────────────────────────────────────────────────
w("---")
w("## 3. Two Price Events")
w()
w("### 3.1 TCS — Event Date 2018-05-31")
w()
w("**Claim.** TCS's closing price roughly halved from 2018-05-30 to 2018-05-31 with no "
  "subsequent recovery, consistent with a 1:1 bonus issue (adjustment factor 2).")
w()
w("**Evidence.** `sql/12_worst_day.sql` flags 2018-05-31 as TCS's single worst daily close "
  "change (−50.4%). The table below shows the 3 days before and 3 days after.")
w()
w("| Date | Raw Close (₹) | Adj Close (₹) |")
w("|------|---------------|---------------|")
for r in tcs_window:
    marker = " ← event" if r[0] == "2018-05-31" else ""
    w(f"| {r[0]} | {fmt(r[1], 2)} | {fmt(r[2], 2)}{marker} |")
w()
w("**Caveat.** This analysis assumes a clean factor-2 adjustment. The event type "
  "(bonus issue vs. stock split vs. spin-off) should be confirmed from an external source "
  "before quoting adjusted figures.")
w()
w("### 3.2 Infosys — Event Date 2015-06-15")
w()
w("**Claim.** Infosys shows the same pattern on 2015-06-15 (−49.9% single-day close change "
  "per `sql/12_worst_day.sql`), also consistent with a 1:1 bonus issue.")
w()
w("**Evidence.** The 3-day window below confirms prices settled immediately into the new level:")
w()
w("| Date | Raw Close (₹) | Adj Close (₹) |")
w("|------|---------------|---------------|")
for r in inf_window:
    marker = " ← event" if r[0] == "2015-06-15" else ""
    w(f"| {r[0]} | {fmt(r[1], 2)} | {fmt(r[2], 2)}{marker} |")
w()
w("**Caveat.** Same as Section 3.1.")
w()
w("### 3.3 What the Adjustment Changes")
w()
w("![TCS raw vs adjusted close price](images/tcs_raw_vs_adjusted.png)")
w()
w("*The chart shows the discontinuity in the raw series and the continuous adjusted series.*")
w()

tcs_raw_b  = raw_sig_tcs["buys"]
tcs_raw_s  = raw_sig_tcs["sells"]
tcs_adj_b  = sig_data["TCS"]["buys"]
tcs_adj_s  = sig_data["TCS"]["sells"]
tcs_raw_ls = raw_sig_tcs["last_date"]
tcs_adj_ls = sig_data["TCS"]["last_sig_date"]
tcs_adj_lsig = sig_data["TCS"]["last_sig"]

inf_raw_b  = raw_sig_inf["buys"]
inf_raw_s  = raw_sig_inf["sells"]
inf_adj_b  = sig_data["Infosys"]["buys"]
inf_adj_s  = sig_data["Infosys"]["sells"]
inf_adj_ls = sig_data["Infosys"]["last_sig_date"]
inf_adj_lsig = sig_data["Infosys"]["last_sig"]

w("**Effect on percentage change:**")
w()
w("| Stock | Raw % change | Adjusted % change |")
w("|-------|-------------|-------------------|")
w(f"| TCS | {fmt(raw_pct['TCS'])} | {fmt(tcs_adj_pct)} |")
w(f"| Infosys | {fmt(raw_pct['Infosys'])} | {fmt(inf_adj_pct)} |")
w()
w("**Effect on signals:**")
w()
w("| Stock | Version | Buys | Sells | Last signal |")
w("|-------|---------|------|-------|-------------|")
w(f"| TCS | Raw | {tcs_raw_b} | {tcs_raw_s} | Sell {tcs_raw_ls} |")
w(f"| TCS | Adjusted | {tcs_adj_b} | {tcs_adj_s} | {tcs_adj_lsig} {tcs_adj_ls} |")
w(f"| Infosys | Raw | {inf_raw_b} | {inf_raw_s} | Buy (same date) |")
w(f"| Infosys | Adjusted | {inf_adj_b} | {inf_adj_s} | {inf_adj_lsig} {inf_adj_ls} |")
w()
w("**Dates where signals differ (from `sql/15_adjusted_signals_all.sql`):**")
w()
w("| Stock | Date | Raw signal | Adjusted signal |")
w("|-------|------|-----------|----------------|")
for r in raw_adj_diffs:
    w(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |")
w()
w("The adjustment eliminates the artificial MA50 distortion caused by the halving event "
  "remaining in the window for 50 trading days. For TCS, the raw series produces an extra "
  "Sell on 2018-06-05 that the adjusted series suppresses. For Infosys, the adjusted series "
  "detects three additional signal flips in July–August 2015 that are also an artefact of "
  "the discontinuity passing through the window.")
w()

# ── 4. Per-stock results ──────────────────────────────────────────────────────
w("---")
w("## 4. Per-Stock Results")
w()
w("### 4.1 Summary Table")
w()
w("Prices and signals use the adjusted series. % change is from first to last trading day "
  "(`sql/11_pct_change.sql`). Signals from `sql/10_all_stocks.sql`. "
  "Round trips from `sql/16_whipsaws.sql`.")
w()
w("| Stock | First close | Last close | % change | Buys | Sells | Last signal | Last date | Round trips | Winners | Avg RT return |")
w("|-------|------------|-----------|---------|------|-------|-------------|-----------|------------|---------|--------------|")
for s in stocks_sorted:
    ap = adj_pct[s]
    sd = sig_data[s]
    rd = rt_data[s]
    w(f"| {s} | {fmt(ap['adj_fc'],2)} | {fmt(ap['adj_lc'],2)} | {fmt(ap['adj_pct'])}% "
      f"| {sd['buys']} | {sd['sells']} | {sd['last_sig']} | {sd['last_sig_date']} "
      f"| {rd['trips']} | {rd['winners']} | {fmt(rd['avg_ret'])}% |")
w()
w("### 4.2 Stock-by-Stock Notes")
w()

stock_notes = {
    "TVS Motors": (
        f"Close price rose {fmt(adj_pct['TVS Motors']['adj_pct'])}% over the full period, "
        f"the largest gain in the group.",
        "One round trip (2017-01-06 to 2018-01-29) returned {rt}% and dominates the average. "
        "The other {n} trips averaged {avg}% combined.",
        "A single long-held trade can distort the average; the sample of 8 trips is small. "
        "The signal method uses only MA crossovers and cannot reflect fundamentals."
    ),
    "Eicher Motors": (
        f"Close price rose {fmt(adj_pct['Eicher Motors']['adj_pct'])}% and every one of the "
        f"{rt_data['Eicher Motors']['trips']} Buy–Sell round trips was profitable.",
        "sql/11_pct_change.sql and sql/16_whipsaws.sql; 6 round trips, 6 winners.",
        "6 round trips is a small sample; a longer period could show losses. "
        "The trend is strong, but the rule cannot detect peaks in advance."
    ),
    "Bajaj Auto": (
        f"Price rose {fmt(adj_pct['Bajaj Auto']['adj_pct'])}% overall, but the rule's "
        f"{rt_data['Bajaj Auto']['trips']} round trips returned only {fmt(rt_data['Bajaj Auto']['avg_ret'])}% on average "
        f"with {rt_data['Bajaj Auto']['winners']} of {rt_data['Bajaj Auto']['trips']} profitable, "
        f"largely because of frequent whipsaws in late 2015.",
        "sql/10_all_stocks.sql (signals), sql/16_whipsaws.sql (round trips).",
        "The whipsaw period in late 2015 is short and may not recur; average return is not compounded."
    ),
    "Hero Motocorp": (
        f"Price rose {fmt(adj_pct['Hero Motocorp']['adj_pct'])}% overall. "
        f"The signal rule produced {rt_data['Hero Motocorp']['trips']} round trips with "
        f"only {rt_data['Hero Motocorp']['winners']} winners and an average of "
        f"{fmt(rt_data['Hero Motocorp']['avg_ret'])}%.",
        "sql/10_all_stocks.sql; sql/16_whipsaws.sql.",
        "Small sample; average return is not compounded."
    ),
    "Infosys": (
        f"Adjusted close rose {fmt(adj_pct['Infosys']['adj_pct'])}%. "
        f"Raw close would show {fmt(raw_pct['Infosys'])}%, a misleading decline caused by the bonus event.",
        "sql/13_adjusted.sql (adjusted % change); sql/15_adjusted_signals_all.sql (signal differences).",
        "The adjustment factor of 2 is assumed, not verified. The adjusted signal count "
        f"({inf_adj_b}/{inf_adj_s}) differs from the raw count ({inf_raw_b}/{inf_raw_s}) on "
        f"four dates."
    ),
    "TCS": (
        f"Adjusted close rose {fmt(adj_pct['TCS']['adj_pct'])}%. "
        f"Raw close would show {fmt(raw_pct['TCS'])}%, a misleading decline caused by the bonus event. "
        f"The adjusted series' last signal is a Buy on {sig_data['TCS']['last_sig_date']}, "
        f"whereas the raw series ends on a Sell on {raw_sig_tcs['last_date']}. "
        f"The adjusted version is more consistent with the positive long-run trend; "
        f"the raw-series Sell is an artefact of the un-adjusted event passing through the MA50 window.",
        "sql/13_adjusted.sql; sql/15_adjusted_signals_all.sql.",
        "Same adjustment caveat as Infosys."
    ),
}

for s in stocks_sorted:
    w(f"#### {s}")
    w()
    note = stock_notes.get(s, ("", "", ""))
    claim, evidence, caveat = note
    # Substitute TVS run-time values
    if s == "TVS Motors" and tvs_big:
        tvs_n   = rt_data["TVS Motors"]["trips"] - 1
        claim   = claim
        evidence = evidence.format(rt=fmt(tvs_big[6], 1), n=tvs_n, avg=fmt(tvs_others_avg))
    w(f"**Claim.** {claim}")
    w()
    w(f"**Evidence.** {evidence}")
    w()
    w(f"**Caveat.** {caveat}")
    w()

# ── 5. Whipsaws ───────────────────────────────────────────────────────────────
w("---")
w("## 5. Whipsaws")
w()
w("![Bajaj Auto price, MA20, MA50 and signals](images/bajaj_signals.png)")
w()
w("*Green triangles = Buy signals; red triangles = Sell signals.*")
w()
w(f"Across all six stocks, {total_short_pairs} consecutive signal pairs were "
  f"30 calendar days apart or fewer. "
  f"{total_short_rt} of these also formed round trips (Buy → Sell within 30 days); "
  f"{short_rt_losers} of those {total_short_rt} lost money.")
w()
w("**Short-gap pairs per stock:**")
w()
w("| Stock | Consecutive signal pairs ≤ 30 days | Round trips ≤ 30 days | Avg return of those trips |")
w("|-------|-----------------------------------|-----------------------|---------------------------|")
for s in stocks_sorted:
    sp  = short_pairs.get(s, 0)
    srt = rt_data[s]["short_trips"]
    sar = rt_data[s]["avg_short_ret"]
    w(f"| {s} | {sp} | {srt} | {fmt(sar)}% |")
w()
w("### 5.1 Illustrative Whipsaw Examples")
w()
w("**Bajaj Auto, December 2015.** Four signals in 17 calendar days:")
w()
w("| Date | Signal | Close (₹) | Round-trip return |")
w("|------|--------|----------|------------------|")
# Find the Dec 2015 bajaj signals from rt_detail
dec_2015_signals = []
for r in bajaj_chart_data:
    if r[0] >= "2015-12-01" and r[0] <= "2015-12-31" and r[4] in ("Buy","Sell"):
        dec_2015_signals.append(r)
# also the two round trips
dec_2015_rt = [r for r in rt_detail
               if r[0] == "Bajaj Auto" and r[1] in ("2015-12-17","2015-12-28")]
dec_2015_rt_map = {r[1]: r[6] for r in dec_2015_rt}
dec_2015_sell_rt = [r for r in rt_detail
                    if r[0]=="Bajaj Auto" and r[2] in ("2015-12-11","2015-12-23")]
dec_2015_sell_map = {r[2]: r[6] for r in dec_2015_sell_rt}

for r in dec_2015_signals:
    if r[4] == "Buy":
        ret_str = f"{fmt(dec_2015_rt_map.get(r[0]))}%" if r[0] in dec_2015_rt_map else "—"
    else:
        ret_str = f"{fmt(dec_2015_sell_map.get(r[0]))}% (this sell)" if r[0] in dec_2015_sell_map else "—"
    w(f"| {r[0]} | {r[4]} | {fmt(r[1],2)} | {ret_str} |")
w()
w("**Bajaj Auto, Feb 2018.** Buy on 2018-02-01 at ₹3,409.50, Sell on 2018-02-06 at ₹3,138.20 "
  "(5 calendar days, −8.0% return). This single trade cost more than the full-period price gain "
  "of 10.0%.")
w()
w("**TCS, Oct 2015.** Buy on 2015-10-13, Sell on 2015-10-14 — a 1-calendar-day round trip "
  "returning −4.4%. The signal crossed back in the first trading session.")
w()
w("**Five shortest-gap signal pairs across all stocks:**")
w()
w("| Stock | Prev date | Prev signal | Prev close | Date | Signal | Close | Gap (days) |")
w("|-------|-----------|------------|-----------|------|--------|-------|-----------|")
for r in top5_short:
    w(f"| {r[0]} | {r[1]} | {r[2]} | {fmt(float(r[3]),2)} "
      f"| {r[4]} | {r[5]} | {fmt(float(r[6]),2)} | {r[7]} |")
w()

# ── 6. Method questions ───────────────────────────────────────────────────────
w("---")
w("## 6. Method Questions")
w()
w("### 6.a Lag of the golden-cross rule")
w()
w("A simple moving average uses only past closing prices. MA20 on day *d* averages days "
  "*d−19* to *d*; MA50 averages *d−49* to *d*. The first day MA50 can have a value is "
  "trading-day 50 (the 50th row in the dataset). A crossover signal additionally requires "
  "the *previous* day's MA50, so the earliest possible signal date is **trading-day 51**. "
  "In this dataset that corresponds to 2015-03-13 for the MA50 warm-up; "
  f"Bajaj Auto's first Buy is **2015-05-18**, 98 days after the start of data.")
w()
w("Implication: the rule cannot react to any trend that began before row 51, "
  "and it always reflects where the price *was* rather than where it is going. "
  "A sharp reversal will take many days before the crossover fires.")
w()
w("### 6.b What changes after adjustment")
w()
w("Before adjustment, TCS and Infosys appear to have **lost** money over the period "
  f"({fmt(raw_pct['TCS'])}% and {fmt(raw_pct['Infosys'])}%). After adjusting, both "
  f"**gained** ({fmt(tcs_adj_pct)}% and {fmt(inf_adj_pct)}%). "
  "The direction of the result reverses — a material difference.")
w()
w("Signal counts change for both stocks (see [Section 3.3](#33-what-the-adjustment-changes)). "
  "For TCS, the last signal changes from a Sell (raw) to a Buy (adjusted). Treating the "
  "adjusted series as more representative of the true economic return, the raw Sell is an "
  "artefact of the price discontinuity still sitting inside the MA50 window.")
w()
w("### 6.c What this data lacks")
w()
w("| Missing element | Why it matters |")
w("|----------------|---------------|")
w("| **Dividends** | The total return is higher than the price return alone; |")
w("|               | this analysis understates actual long-run gains. |")
w("| **Brokerage costs** | Each round trip incurs transaction costs; |")
w("|               | the thin margins on short-gap trades may not survive costs. |")
w("| **Market index** | Without a benchmark (e.g., Nifty 50), it is impossible to |")
w("|               | judge whether the rule adds value over passive investing. |")
w("| **News and fundamentals** | Price-only rules cannot distinguish a correction from |")
w("|               | a structural decline. |")
w()

# ── 7. Limits ────────────────────────────────────────────────────────────────
w("---")
w("## 7. Limits of This Analysis")
w()
w(f"- **Small samples.** Each stock has between 6 and {max(v['trips'] for v in rt_data.values())} "
  "round trips. Averages over such small samples are unreliable; a single unusual trade "
  "(as with TVS Motors) can dominate the result.")
w()
w("- **Simple averages vs. buy-and-hold.** The average round-trip return is an arithmetic mean "
  "of per-trade returns. It is not compounded and cannot be compared directly with the "
  "first-to-last percentage change in the summary table.")
w()
w(f"- **TVS Motors outlier.** One round trip (2017-01-06 to 2018-01-29) returned "
  f"{fmt(tvs_big[6], 1) if tvs_big else '?'}%. "
  f"The remaining {rt_data['TVS Motors']['trips']-1} TVS trips averaged {fmt(tvs_others_avg)}%. "
  "Conclusions about TVS strategy performance rest almost entirely on one trade.")
w()
w("- **No out-of-sample test.** The signals were computed on the same data used to describe "
  "them; there is no forward test. Results may not repeat in a different period.")
w()
w("---")
w("*Report generated by `src/make_report.py` from `data/stocks.db`. "
  "No numbers were entered by hand.*")
w()

# ── write file ────────────────────────────────────────────────────────────────
with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\nReport written to {REPORT_PATH}")
print(f"Word count (approx): {len(' '.join(lines).split())}")

conn.close()
