# Stock Market Analysis in SQL

Analysis of six NSE stocks (Bajaj Auto, Eicher Motors, Hero Motocorp, Infosys, TCS, TVS Motors), 889 trading days each, 2015-01-01 to 2018-07-31. It computes 20-day and 50-day moving averages, derives golden-cross Buy/Sell/Hold signals, adjusts prices for two overnight price halvings (inferred bonus issues), and studies whipsaws and round trips.

The analysis was developed and cross-checked in SQLite, then ported to MySQL 8, which is the submitted version.

## Deliverables

| Deliverable | Where |
|---|---|
| SQL analysis, single .txt file (MySQL 8) | `submission/stock_market_analysis.txt` |
| Insights report (Markdown) | `reports/insights.md` |
| Insights report (PDF) | delivered separately |
| Video walkthrough (narration script) | delivered separately |

## Repository layout

```
data/          six source CSV files and the generated SQLite database (see .gitignore)
sql/           16 SQLite task files, one per task (01_... to 16_...)
src/           Python loaders, task runners and report builder for the SQLite pipeline
reports/       insights.md and images/ (charts)
mysql/         MySQL 8 port
  00_setup.sql           DROP/CREATE TABLE and LOAD DATA (data path is a placeholder)
  stock_analysis.sql     tasks 1-16 for MySQL
  db_up.sh               starts a Podman mysql:8.4 container bound to 127.0.0.1
  run_setup.sh           runs 00_setup.sql with the data path filled in
  mysql_cli.sh           mysql client wrapper that reads credentials from mysql/.env
  build_submission.sh    regenerates submission/stock_market_analysis.txt
  run_checks.sh          starts the container, then runs the two checkers
  verify_load.py, verify_checkpoints.py, verify_parity.py
submission/    stock_market_analysis.txt
```

`mysql/.env` and the SQLite database are git-ignored and never committed.

## Running it

### MySQL 8 (the submission)

1. Open `submission/stock_market_analysis.txt` and replace `/PATH/TO/CSV/` in the six `LOAD DATA` statements with the folder holding the six CSV files (keep the trailing slash).
2. Enable local loading on the server: `SET GLOBAL local_infile = 1;`
3. Run it on MySQL 8: `mysql --local-infile=1 -u root -p < submission/stock_market_analysis.txt`, or open it in MySQL Workbench and execute it. It creates the database `stock_analysis`, drops and recreates the tables, loads the data and runs all tasks. It can be run repeatedly.

### Local container (development)

1. Create `mysql/.env` (git-ignored, `chmod 600`) with `MYSQL_ROOT_PASSWORD=<choose one>` and `MYSQL_DATABASE=stock_analysis`.
2. `bash mysql/db_up.sh` starts the container.
3. `bash mysql/run_setup.sh` creates and loads the tables.
4. `./mysql/mysql_cli.sh stock_analysis < mysql/stock_analysis.sql` runs the analysis.
5. `bash mysql/run_checks.sh stock_analysis` runs the checkers (needs `pip install pymysql`).
6. After editing `00_setup.sql` or `stock_analysis.sql`, run `bash mysql/build_submission.sh` to regenerate the .txt.

### SQLite (development and cross-check)

`python3 src/load_sqlite.py` loads the CSVs into the SQLite database; `python3 src/run_task10.py` (and the other `src/run_*.py` scripts) run the task queries; `python3 src/make_report.py` rebuilds `reports/insights.md` and the charts; `python3 src/verify_report.py` checks the report's figures. Charts need `matplotlib`.

## Method

- **Signal rule.** Buy when MA20 > MA50 today and MA20 <= MA50 yesterday; Sell on the opposite crossing; every other day is Hold. MA20 and MA50 are NULL until 20 and 50 rows exist, so the first 50 days are always Hold. Averages are unrounded; rounding happens only in final SELECTs.
- **Tasks.** Tasks 1-13 follow the course guide (headers are in `mysql/stock_analysis.sql`). Extension tasks: 14 TCS adjusted signals, 15 all-stock adjusted signals, 16 whipsaws and round trips.
- **Price adjustment.** TCS on 2018-05-31 and Infosys on 2015-06-15 show a close that roughly halves overnight and stays lower. Closes before each date are divided by 2. This treats the events as 1:1 bonus issues, which is inferred from the price pattern and the course material, not confirmed against company announcements.

## Key results

| Stock | Buys | Sells | Holds | Last signal | Date |
|---|---|---|---|---|---|
| Bajaj Auto | 12 | 11 | 866 | Buy | 2018-06-21 |
| Eicher Motors | 6 | 7 | 876 | Sell | 2018-06-06 |
| Hero Motocorp | 9 | 9 | 871 | Sell | 2018-05-22 |
| Infosys | 9 | 9 | 871 | Buy | 2018-05-07 |
| TCS | 12 | 13 | 864 | Sell | 2018-06-05 |
| TVS Motors | 8 | 8 | 873 | Sell | 2018-05-17 |

These are the unadjusted signals (task 10). TCS and Infosys signals after the price adjustment are in tasks 14 and 15.

Round trips (a Buy followed by the next Sell), adjusted series for TCS and Infosys:

| Stock | Round trips | Winners | Avg return % |
|---|---|---|---|
| Bajaj Auto | 11 | 4 | 0.4 |
| Eicher Motors | 6 | 6 | 10.2 |
| Hero Motocorp | 9 | 3 | -1.7 |
| Infosys | 9 | 3 | -0.4 |
| TCS | 11 | 2 | -3.4 |
| TVS Motors | 8 | 3 | 11.2 |

## Verification

- `verify_load.py` checks row counts, date bounds and NULL counts after loading.
- `verify_checkpoints.py` checks task results against the expected values.
- `verify_parity.py` compares MySQL results with the SQLite results.
- Run the checkers yourself before relying on them; they need the container running and `pymysql` installed.

## Limitations

- No signal can appear in the first 50 trading days.
- Brokerage costs and dividends are excluded.
- The bonus-issue factor is an assumption (see Method).
- MySQL uses exact DECIMAL, SQLite uses floating point; the two agreed on the values compared.
- Two statements in the course deck do not match the data (TCS price labels, the Infosys "3%" figure); `reports/insights.md` notes this.

## Security

No credentials are committed. `mysql/.env` is git-ignored and should be `chmod 600`. The container publishes its port on 127.0.0.1 only.