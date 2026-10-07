-- ==============================================================================
-- Stock Analysis: MySQL 8 Port
-- Expects the six tables (bajaj_auto, eicher_motors, hero_motocorp, infosys, tcs, tvs_motors)
-- to be loaded per mysql/00_setup.sql.
-- Runs top to bottom on a fresh database.
-- ==============================================================================

-- ===== Task 1: Dataset Overview (sql/01_history.sql) =====
SELECT
    COUNT(*) AS trading_days,
    MIN(`date`) AS first_day,
    MAX(`date`) AS last_day
FROM bajaj_auto;


-- ===== Task 2: Eicher Motors Top 5 Close Prices (sql/02_eicher_top5.sql) =====
SELECT
    `date`,
    close_price
FROM eicher_motors
ORDER BY close_price DESC
LIMIT 5;


-- ===== Task 3: TCS Yearly Average Close Price (sql/03_tcs_yearly.sql) =====
SELECT
    YEAR(`date`) AS year,
    ROUND(AVG(close_price), 2) AS avg_close_price
FROM tcs
GROUP BY YEAR(`date`)
ORDER BY year ASC;


-- ===== Task 4: Missing Deliverable Quantity Dates (sql/04_null_deliverable.sql) =====
SELECT 'bajaj_auto' AS stock, `date` FROM bajaj_auto WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'eicher_motors' AS stock, `date` FROM eicher_motors WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'hero_motocorp' AS stock, `date` FROM hero_motocorp WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'infosys' AS stock, `date` FROM infosys WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'tcs' AS stock, `date` FROM tcs WHERE deliverable_qty IS NULL
UNION ALL
SELECT 'tvs_motors' AS stock, `date` FROM tvs_motors WHERE deliverable_qty IS NULL;


-- ===== Task 5: Bajaj Auto 20-Day and 50-Day Moving Averages (sql/05_moving_averages.sql) =====
DROP TABLE IF EXISTS bajaj1;
CREATE TABLE bajaj1 AS
SELECT
    `date`,
    close_price,
    CASE
        WHEN ROW_NUMBER() OVER (ORDER BY `date`) >= 20
        THEN ROUND(AVG(close_price) OVER (ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 2)
        ELSE NULL
    END AS ma20,
    CASE
        WHEN ROW_NUMBER() OVER (ORDER BY `date`) >= 50
        THEN ROUND(AVG(close_price) OVER (ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW), 2)
        ELSE NULL
    END AS ma50
FROM bajaj_auto
ORDER BY `date`;


-- ===== Task 6: Master Table of Close Prices (sql/06_master_table.sql) =====
DROP TABLE IF EXISTS master_table;
CREATE TABLE master_table AS
SELECT
    b.`date`,
    b.close_price AS bajaj,
    tcs.close_price AS tcs,
    tvs.close_price AS tvs,
    inf.close_price AS infosys,
    eic.close_price AS eicher,
    her.close_price AS hero
FROM bajaj_auto b
JOIN tcs ON b.`date` = tcs.`date`
JOIN tvs_motors tvs ON b.`date` = tvs.`date`
JOIN infosys inf ON b.`date` = inf.`date`
JOIN eicher_motors eic ON b.`date` = eic.`date`
JOIN hero_motocorp her ON b.`date` = her.`date`
ORDER BY b.`date`;


-- ===== Task 7: Bajaj Auto Golden-Cross Signals (sql/07_signals.sql) =====
DROP TABLE IF EXISTS bajaj2;
CREATE TABLE bajaj2 AS
WITH t AS (
    SELECT
        `date`,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (ORDER BY `date`) AS prev_ma20,
        LAG(ma50) OVER (ORDER BY `date`) AS prev_ma50
    FROM bajaj1
)
SELECT
    `date`,
    close_price,
    CASE
        WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
        WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
        WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
        ELSE 'Hold'
    END AS `signal`
FROM t
ORDER BY `date`;


-- ===== Task 8: Bajaj Auto Signal Counts (sql/08_signal_counts.sql) =====
SELECT
    `signal`,
    COUNT(*) AS count
FROM bajaj2
GROUP BY `signal`
ORDER BY `signal`;


-- ===== Task 9: Bajaj Auto Signal on Date and User Defined Function (sql/09_signal_on_date.sql) =====
SELECT
    `date`,
    `signal`
FROM bajaj2
WHERE `date` = '2018-06-21';

DROP FUNCTION IF EXISTS bajaj_signal;
DELIMITER $$
-- bajaj_signal returns 'Buy', 'Sell', or 'Hold' for Bajaj Auto on a given date.
-- It returns NULL when the date has no row (e.g. weekends or holidays when market is closed).
CREATE FUNCTION bajaj_signal(d DATE)
RETURNS VARCHAR(10)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE res VARCHAR(10) DEFAULT NULL;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET res = NULL;
    SELECT `signal` INTO res
    FROM bajaj2
    WHERE `date` = d;
    RETURN res;
END$$
DELIMITER ;


-- ===== Task 10: Signal Counts and Last Signal for All Stocks (sql/10_all_stocks.sql) =====
WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
    UNION ALL
    SELECT 'Eicher Motors' AS stock, `date`, close_price FROM eicher_motors
    UNION ALL
    SELECT 'Hero Motocorp' AS stock, `date`, close_price FROM hero_motocorp
    UNION ALL
    SELECT 'Infosys' AS stock, `date`, close_price FROM infosys
    UNION ALL
    SELECT 'TCS' AS stock, `date`, close_price FROM tcs
    UNION ALL
    SELECT 'TVS Motors' AS stock, `date`, close_price FROM tvs_motors
),
ma AS (
    SELECT
        stock,
        `date`,
        close_price,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 20
            THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma20,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 50
            THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma50
    FROM prices
),
lagged AS (
    SELECT
        stock,
        `date`,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma20,
        LAG(ma50) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT
        stock,
        `date`,
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
        `date` AS last_signal_date,
        `signal` AS last_signal,
        ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date` DESC) AS rn
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


-- ===== Task 11: Percentage Change in Close Price (sql/11_pct_change.sql) =====
WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
    UNION ALL
    SELECT 'Eicher Motors' AS stock, `date`, close_price FROM eicher_motors
    UNION ALL
    SELECT 'Hero Motocorp' AS stock, `date`, close_price FROM hero_motocorp
    UNION ALL
    SELECT 'Infosys' AS stock, `date`, close_price FROM infosys
    UNION ALL
    SELECT 'TCS' AS stock, `date`, close_price FROM tcs
    UNION ALL
    SELECT 'TVS Motors' AS stock, `date`, close_price FROM tvs_motors
),
ends AS (
    SELECT
        stock,
        MIN(`date`) AS first_date,
        MAX(`date`) AS last_date
    FROM prices
    GROUP BY stock
)
SELECT
    e.stock,
    p_first.close_price AS first_close,
    p_last.close_price AS last_close,
    ROUND(100.0 * (p_last.close_price - p_first.close_price) / p_first.close_price, 1) AS pct_change
FROM ends e
JOIN prices p_first ON e.stock = p_first.stock AND e.first_date = p_first.`date`
JOIN prices p_last ON e.stock = p_last.stock AND e.last_date = p_last.`date`
ORDER BY pct_change DESC;


-- ===== Task 12: Single Worst Day per Stock (sql/12_worst_day.sql) =====
WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
    UNION ALL
    SELECT 'Eicher Motors' AS stock, `date`, close_price FROM eicher_motors
    UNION ALL
    SELECT 'Hero Motocorp' AS stock, `date`, close_price FROM hero_motocorp
    UNION ALL
    SELECT 'Infosys' AS stock, `date`, close_price FROM infosys
    UNION ALL
    SELECT 'TCS' AS stock, `date`, close_price FROM tcs
    UNION ALL
    SELECT 'TVS Motors' AS stock, `date`, close_price FROM tvs_motors
),
daily AS (
    SELECT
        stock,
        `date`,
        close_price,
        LAG(close_price) OVER (PARTITION BY stock ORDER BY `date`) AS prev_close
    FROM prices
),
moves AS (
    SELECT
        stock,
        `date`,
        close_price,
        100.0 * (close_price / prev_close - 1) AS pct_move
    FROM daily
    WHERE prev_close IS NOT NULL
),
ranked AS (
    SELECT
        stock,
        `date`,
        close_price,
        pct_move,
        ROW_NUMBER() OVER (PARTITION BY stock ORDER BY pct_move ASC) AS rn
    FROM moves
)
SELECT
    stock,
    `date`,
    close_price,
    ROUND(pct_move, 1) AS pct_move
FROM ranked
WHERE rn = 1
ORDER BY pct_move ASC;


-- ===== Task 13: TCS and Infosys Corporate Action Adjusted Return (sql/13_adjusted.sql) =====
WITH adjusted AS (
    SELECT
        'TCS' AS stock,
        `date`,
        CASE
            WHEN `date` < '2018-05-31' THEN close_price / 2.0
            ELSE close_price
        END AS adj_close
    FROM tcs
    UNION ALL
    SELECT
        'Infosys' AS stock,
        `date`,
        CASE
            WHEN `date` < '2015-06-15' THEN close_price / 2.0
            ELSE close_price
        END AS adj_close
    FROM infosys
)
SELECT
    stock,
    ROUND(
        100.0 * (
            MAX(CASE WHEN `date` = '2018-07-31' THEN adj_close END) -
            MAX(CASE WHEN `date` = '2015-01-01' THEN adj_close END)
        ) / MAX(CASE WHEN `date` = '2015-01-01' THEN adj_close END),
        1
    ) AS adjusted_pct_change
FROM adjusted
GROUP BY stock
ORDER BY stock;


-- ===== Extension =====

-- ===== Task 14: TCS Raw vs Adjusted Signals (sql/14_tcs_adjusted_signals.sql) =====
WITH tcs_series AS (
    SELECT 'raw' AS version, `date`, close_price FROM tcs
    UNION ALL
    SELECT 'adjusted' AS version, `date`, CASE WHEN `date` < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS close_price FROM tcs
),
ma AS (
    SELECT
        version,
        `date`,
        close_price,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY version ORDER BY `date`) >= 20
            THEN AVG(close_price) OVER (PARTITION BY version ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma20,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY version ORDER BY `date`) >= 50
            THEN AVG(close_price) OVER (PARTITION BY version ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma50
    FROM tcs_series
),
lagged AS (
    SELECT
        version,
        `date`,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (PARTITION BY version ORDER BY `date`) AS prev_ma20,
        LAG(ma50) OVER (PARTITION BY version ORDER BY `date`) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT
        version,
        `date`,
        close_price,
        CASE
            WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
            WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
            WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
            ELSE 'Hold'
        END AS `signal`
    FROM lagged
)
SELECT
    r.`date`,
    r.`signal` AS raw_signal,
    a.`signal` AS adj_signal
FROM (SELECT `date`, `signal` FROM sig WHERE version = 'raw') r
JOIN (SELECT `date`, `signal` FROM sig WHERE version = 'adjusted') a ON r.`date` = a.`date`
WHERE r.`signal` != a.`signal`
ORDER BY r.`date`;


-- ===== Task 15: Generalised Raw vs Adjusted Signals for TCS and Infosys (sql/15_adjusted_signals_all.sql) =====

-- Section 1: Buys and Sells per stock per version
WITH combined_series AS (
    SELECT 'TCS' AS stock, 'raw' AS version, `date`, close_price FROM tcs
    UNION ALL
    SELECT 'TCS' AS stock, 'adjusted' AS version, `date`, CASE WHEN `date` < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS close_price FROM tcs
    UNION ALL
    SELECT 'Infosys' AS stock, 'raw' AS version, `date`, close_price FROM infosys
    UNION ALL
    SELECT 'Infosys' AS stock, 'adjusted' AS version, `date`, CASE WHEN `date` < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS close_price FROM infosys
),
ma AS (
    SELECT
        stock,
        version,
        `date`,
        close_price,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY `date`) >= 20
            THEN AVG(close_price) OVER (PARTITION BY stock, version ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma20,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY `date`) >= 50
            THEN AVG(close_price) OVER (PARTITION BY stock, version ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma50
    FROM combined_series
),
lagged AS (
    SELECT
        stock,
        version,
        `date`,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (PARTITION BY stock, version ORDER BY `date`) AS prev_ma20,
        LAG(ma50) OVER (PARTITION BY stock, version ORDER BY `date`) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT
        stock,
        version,
        `date`,
        close_price,
        CASE
            WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
            WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
            WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
            ELSE 'Hold'
        END AS `signal`
    FROM lagged
)
SELECT
    stock,
    version,
    SUM(CASE WHEN `signal` = 'Buy' THEN 1 ELSE 0 END) AS buys,
    SUM(CASE WHEN `signal` = 'Sell' THEN 1 ELSE 0 END) AS sells
FROM sig
GROUP BY stock, version
ORDER BY stock, version;

-- Section 2: Every date where raw and adjusted signals differ
WITH combined_series AS (
    SELECT 'TCS' AS stock, 'raw' AS version, `date`, close_price FROM tcs
    UNION ALL
    SELECT 'TCS' AS stock, 'adjusted' AS version, `date`, CASE WHEN `date` < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS close_price FROM tcs
    UNION ALL
    SELECT 'Infosys' AS stock, 'raw' AS version, `date`, close_price FROM infosys
    UNION ALL
    SELECT 'Infosys' AS stock, 'adjusted' AS version, `date`, CASE WHEN `date` < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS close_price FROM infosys
),
ma AS (
    SELECT
        stock,
        version,
        `date`,
        close_price,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY `date`) >= 20
            THEN AVG(close_price) OVER (PARTITION BY stock, version ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma20,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY `date`) >= 50
            THEN AVG(close_price) OVER (PARTITION BY stock, version ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma50
    FROM combined_series
),
lagged AS (
    SELECT
        stock,
        version,
        `date`,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (PARTITION BY stock, version ORDER BY `date`) AS prev_ma20,
        LAG(ma50) OVER (PARTITION BY stock, version ORDER BY `date`) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT
        stock,
        version,
        `date`,
        close_price,
        CASE
            WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
            WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
            WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
            ELSE 'Hold'
        END AS `signal`
    FROM lagged
)
SELECT
    r.stock,
    r.`date`,
    r.`signal` AS raw_signal,
    a.`signal` AS adj_signal
FROM (SELECT stock, `date`, `signal` FROM sig WHERE version = 'raw') r
JOIN (SELECT stock, `date`, `signal` FROM sig WHERE version = 'adjusted') a
  ON r.stock = a.stock AND r.`date` = a.`date`
WHERE r.`signal` != a.`signal`
ORDER BY r.stock, r.`date`;

-- Section 3: Last non-Hold signal for each stock and version
WITH combined_series AS (
    SELECT 'TCS' AS stock, 'raw' AS version, `date`, close_price FROM tcs
    UNION ALL
    SELECT 'TCS' AS stock, 'adjusted' AS version, `date`, CASE WHEN `date` < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS close_price FROM tcs
    UNION ALL
    SELECT 'Infosys' AS stock, 'raw' AS version, `date`, close_price FROM infosys
    UNION ALL
    SELECT 'Infosys' AS stock, 'adjusted' AS version, `date`, CASE WHEN `date` < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS close_price FROM infosys
),
ma AS (
    SELECT
        stock,
        version,
        `date`,
        close_price,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY `date`) >= 20
            THEN AVG(close_price) OVER (PARTITION BY stock, version ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma20,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY `date`) >= 50
            THEN AVG(close_price) OVER (PARTITION BY stock, version ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma50
    FROM combined_series
),
lagged AS (
    SELECT
        stock,
        version,
        `date`,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (PARTITION BY stock, version ORDER BY `date`) AS prev_ma20,
        LAG(ma50) OVER (PARTITION BY stock, version ORDER BY `date`) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT
        stock,
        version,
        `date`,
        close_price,
        CASE
            WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
            WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
            WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
            ELSE 'Hold'
        END AS `signal`
    FROM lagged
),
ranked_signals AS (
    SELECT
        stock,
        version,
        `date`,
        `signal`,
        ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY `date` DESC) AS rn
    FROM sig
    WHERE `signal` != 'Hold'
)
SELECT
    stock,
    version,
    `date` AS last_signal_date,
    `signal` AS last_signal
FROM ranked_signals
WHERE rn = 1
ORDER BY stock, version;


-- ===== Task 16: Whipsaw and Round-Trip Analysis (sql/16_whipsaws.sql) =====

-- Section 1: Number of consecutive-signal pairs with a gap of 30 days or less per stock
WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
    UNION ALL
    SELECT 'Eicher Motors' AS stock, `date`, close_price FROM eicher_motors
    UNION ALL
    SELECT 'Hero Motocorp' AS stock, `date`, close_price FROM hero_motocorp
    UNION ALL
    SELECT 'Infosys' AS stock, `date`, CASE WHEN `date` < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS close_price FROM infosys
    UNION ALL
    SELECT 'TCS' AS stock, `date`, CASE WHEN `date` < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS close_price FROM tcs
    UNION ALL
    SELECT 'TVS Motors' AS stock, `date`, close_price FROM tvs_motors
),
ma AS (
    SELECT
        stock,
        `date`,
        close_price,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 20
            THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma20,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 50
            THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma50
    FROM prices
),
lagged AS (
    SELECT
        stock,
        `date`,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma20,
        LAG(ma50) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT
        stock,
        `date`,
        close_price,
        CASE
            WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
            WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
            WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
            ELSE 'Hold'
        END AS `signal`
    FROM lagged
),
ledger AS (
    SELECT
        stock,
        `date`,
        `signal`,
        close_price,
        LAG(`date`) OVER (PARTITION BY stock ORDER BY `date`) AS prev_date,
        LAG(`signal`) OVER (PARTITION BY stock ORDER BY `date`) AS prev_signal,
        LAG(close_price) OVER (PARTITION BY stock ORDER BY `date`) AS prev_close,
        DATEDIFF(`date`, LAG(`date`) OVER (PARTITION BY stock ORDER BY `date`)) AS gap_days
    FROM sig
    WHERE `signal` != 'Hold'
)
SELECT
    stock,
    COUNT(CASE WHEN gap_days <= 30 THEN 1 END) AS short_gap_pairs_le_30
FROM ledger
WHERE prev_date IS NOT NULL
GROUP BY stock
ORDER BY stock;

-- Section 2: Round trips summary (Buy followed by Sell) per stock
WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
    UNION ALL
    SELECT 'Eicher Motors' AS stock, `date`, close_price FROM eicher_motors
    UNION ALL
    SELECT 'Hero Motocorp' AS stock, `date`, close_price FROM hero_motocorp
    UNION ALL
    SELECT 'Infosys' AS stock, `date`, CASE WHEN `date` < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS close_price FROM infosys
    UNION ALL
    SELECT 'TCS' AS stock, `date`, CASE WHEN `date` < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS close_price FROM tcs
    UNION ALL
    SELECT 'TVS Motors' AS stock, `date`, close_price FROM tvs_motors
),
ma AS (
    SELECT
        stock,
        `date`,
        close_price,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 20
            THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma20,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 50
            THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma50
    FROM prices
),
lagged AS (
    SELECT
        stock,
        `date`,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma20,
        LAG(ma50) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT
        stock,
        `date`,
        close_price,
        CASE
            WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
            WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
            WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
            ELSE 'Hold'
        END AS `signal`
    FROM lagged
),
ledger AS (
    SELECT
        stock,
        `date`,
        `signal`,
        close_price,
        LAG(`date`) OVER (PARTITION BY stock ORDER BY `date`) AS prev_date,
        LAG(`signal`) OVER (PARTITION BY stock ORDER BY `date`) AS prev_signal,
        LAG(close_price) OVER (PARTITION BY stock ORDER BY `date`) AS prev_close,
        DATEDIFF(`date`, LAG(`date`) OVER (PARTITION BY stock ORDER BY `date`)) AS gap_days
    FROM sig
    WHERE `signal` != 'Hold'
),
round_trips AS (
    SELECT
        stock,
        prev_date AS buy_date,
        `date` AS sell_date,
        prev_close AS buy_close,
        close_price AS sell_close,
        gap_days,
        100.0 * (close_price - prev_close) / prev_close AS ret_pct
    FROM ledger
    WHERE prev_signal = 'Buy' AND `signal` = 'Sell'
)
SELECT
    stock,
    COUNT(*) AS round_trips,
    SUM(CASE WHEN ret_pct > 0 THEN 1 ELSE 0 END) AS winners,
    ROUND(AVG(ret_pct), 1) AS avg_return_pct,
    COUNT(CASE WHEN gap_days <= 30 THEN 1 END) AS round_trips_le_30,
    ROUND(AVG(CASE WHEN gap_days <= 30 THEN ret_pct END), 1) AS avg_return_le_30_pct
FROM round_trips
GROUP BY stock
ORDER BY stock;

-- Section 3: All round trips per stock with percentage return
WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
    UNION ALL
    SELECT 'Eicher Motors' AS stock, `date`, close_price FROM eicher_motors
    UNION ALL
    SELECT 'Hero Motocorp' AS stock, `date`, close_price FROM hero_motocorp
    UNION ALL
    SELECT 'Infosys' AS stock, `date`, CASE WHEN `date` < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS close_price FROM infosys
    UNION ALL
    SELECT 'TCS' AS stock, `date`, CASE WHEN `date` < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS close_price FROM tcs
    UNION ALL
    SELECT 'TVS Motors' AS stock, `date`, close_price FROM tvs_motors
),
ma AS (
    SELECT
        stock,
        `date`,
        close_price,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 20
            THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma20,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 50
            THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma50
    FROM prices
),
lagged AS (
    SELECT
        stock,
        `date`,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma20,
        LAG(ma50) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT
        stock,
        `date`,
        close_price,
        CASE
            WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
            WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
            WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
            ELSE 'Hold'
        END AS `signal`
    FROM lagged
),
ledger AS (
    SELECT
        stock,
        `date`,
        `signal`,
        close_price,
        LAG(`date`) OVER (PARTITION BY stock ORDER BY `date`) AS prev_date,
        LAG(`signal`) OVER (PARTITION BY stock ORDER BY `date`) AS prev_signal,
        LAG(close_price) OVER (PARTITION BY stock ORDER BY `date`) AS prev_close,
        DATEDIFF(`date`, LAG(`date`) OVER (PARTITION BY stock ORDER BY `date`)) AS gap_days
    FROM sig
    WHERE `signal` != 'Hold'
)
SELECT
    stock,
    prev_date AS buy_date,
    `date` AS sell_date,
    prev_close AS buy_close,
    close_price AS sell_close,
    gap_days,
    ROUND(100.0 * (close_price - prev_close) / prev_close, 1) AS ret_pct
FROM ledger
WHERE prev_signal = 'Buy' AND `signal` = 'Sell'
ORDER BY stock, buy_date;

-- Section 4: Top 5 shortest-gap signal pairs across all stocks
WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, `date`, close_price FROM bajaj_auto
    UNION ALL
    SELECT 'Eicher Motors' AS stock, `date`, close_price FROM eicher_motors
    UNION ALL
    SELECT 'Hero Motocorp' AS stock, `date`, close_price FROM hero_motocorp
    UNION ALL
    SELECT 'Infosys' AS stock, `date`, CASE WHEN `date` < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS close_price FROM infosys
    UNION ALL
    SELECT 'TCS' AS stock, `date`, CASE WHEN `date` < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS close_price FROM tcs
    UNION ALL
    SELECT 'TVS Motors' AS stock, `date`, close_price FROM tvs_motors
),
ma AS (
    SELECT
        stock,
        `date`,
        close_price,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 20
            THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma20,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock ORDER BY `date`) >= 50
            THEN AVG(close_price) OVER (PARTITION BY stock ORDER BY `date` ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)
            ELSE NULL
        END AS ma50
    FROM prices
),
lagged AS (
    SELECT
        stock,
        `date`,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma20,
        LAG(ma50) OVER (PARTITION BY stock ORDER BY `date`) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT
        stock,
        `date`,
        close_price,
        CASE
            WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
            WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
            WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
            ELSE 'Hold'
        END AS `signal`
    FROM lagged
),
ledger AS (
    SELECT
        stock,
        prev_date,
        prev_signal,
        prev_close,
        `date`,
        `signal`,
        close_price,
        DATEDIFF(`date`, prev_date) AS gap_days
    FROM (
        SELECT
            stock,
            `date`,
            `signal`,
            close_price,
            LAG(`date`) OVER (PARTITION BY stock ORDER BY `date`) AS prev_date,
            LAG(`signal`) OVER (PARTITION BY stock ORDER BY `date`) AS prev_signal,
            LAG(close_price) OVER (PARTITION BY stock ORDER BY `date`) AS prev_close
        FROM sig
        WHERE `signal` != 'Hold'
    ) s_inner
    WHERE prev_date IS NOT NULL
)
SELECT
    stock,
    prev_date,
    prev_signal,
    prev_close,
    `date`,
    `signal`,
    close_price,
    gap_days
FROM ledger
ORDER BY gap_days ASC, stock ASC, prev_date ASC
LIMIT 5;
