-- Task 15: Generalised raw vs adjusted signal analysis for TCS and Infosys

-- Section 1: Buys and Sells per stock per version
WITH combined_series AS (
    SELECT 'TCS' AS stock, 'raw' AS version, date, close_price FROM tcs
    UNION ALL
    SELECT 'TCS' AS stock, 'adjusted' AS version, date, CASE WHEN date < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS close_price FROM tcs
    UNION ALL
    SELECT 'Infosys' AS stock, 'raw' AS version, date, close_price FROM infosys
    UNION ALL
    SELECT 'Infosys' AS stock, 'adjusted' AS version, date, CASE WHEN date < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS close_price FROM infosys
),
ma AS (
    SELECT
        stock,
        version,
        date,
        close_price,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY date) >= 20
            THEN ROUND(AVG(close_price) OVER (PARTITION BY stock, version ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 2)
            ELSE NULL
        END AS ma20,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY date) >= 50
            THEN ROUND(AVG(close_price) OVER (PARTITION BY stock, version ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW), 2)
            ELSE NULL
        END AS ma50
    FROM combined_series
),
lagged AS (
    SELECT
        stock,
        version,
        date,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (PARTITION BY stock, version ORDER BY date) AS prev_ma20,
        LAG(ma50) OVER (PARTITION BY stock, version ORDER BY date) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT
        stock,
        version,
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
    SELECT 'TCS' AS stock, 'raw' AS version, date, close_price FROM tcs
    UNION ALL
    SELECT 'TCS' AS stock, 'adjusted' AS version, date, CASE WHEN date < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS close_price FROM tcs
    UNION ALL
    SELECT 'Infosys' AS stock, 'raw' AS version, date, close_price FROM infosys
    UNION ALL
    SELECT 'Infosys' AS stock, 'adjusted' AS version, date, CASE WHEN date < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS close_price FROM infosys
),
ma AS (
    SELECT
        stock,
        version,
        date,
        close_price,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY date) >= 20
            THEN ROUND(AVG(close_price) OVER (PARTITION BY stock, version ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 2)
            ELSE NULL
        END AS ma20,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY date) >= 50
            THEN ROUND(AVG(close_price) OVER (PARTITION BY stock, version ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW), 2)
            ELSE NULL
        END AS ma50
    FROM combined_series
),
lagged AS (
    SELECT
        stock,
        version,
        date,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (PARTITION BY stock, version ORDER BY date) AS prev_ma20,
        LAG(ma50) OVER (PARTITION BY stock, version ORDER BY date) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT
        stock,
        version,
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
SELECT
    r.stock,
    r.date,
    r.`signal` AS raw_signal,
    a.`signal` AS adj_signal
FROM (SELECT stock, date, `signal` FROM sig WHERE version = 'raw') r
JOIN (SELECT stock, date, `signal` FROM sig WHERE version = 'adjusted') a
  ON r.stock = a.stock AND r.date = a.date
WHERE r.`signal` != a.`signal`
ORDER BY r.stock, r.date;

-- Section 3: Last non-Hold signal for each stock and version
WITH combined_series AS (
    SELECT 'TCS' AS stock, 'raw' AS version, date, close_price FROM tcs
    UNION ALL
    SELECT 'TCS' AS stock, 'adjusted' AS version, date, CASE WHEN date < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS close_price FROM tcs
    UNION ALL
    SELECT 'Infosys' AS stock, 'raw' AS version, date, close_price FROM infosys
    UNION ALL
    SELECT 'Infosys' AS stock, 'adjusted' AS version, date, CASE WHEN date < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS close_price FROM infosys
),
ma AS (
    SELECT
        stock,
        version,
        date,
        close_price,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY date) >= 20
            THEN ROUND(AVG(close_price) OVER (PARTITION BY stock, version ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 2)
            ELSE NULL
        END AS ma20,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY date) >= 50
            THEN ROUND(AVG(close_price) OVER (PARTITION BY stock, version ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW), 2)
            ELSE NULL
        END AS ma50
    FROM combined_series
),
lagged AS (
    SELECT
        stock,
        version,
        date,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (PARTITION BY stock, version ORDER BY date) AS prev_ma20,
        LAG(ma50) OVER (PARTITION BY stock, version ORDER BY date) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT
        stock,
        version,
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
ranked_signals AS (
    SELECT
        stock,
        version,
        date,
        `signal`,
        ROW_NUMBER() OVER (PARTITION BY stock, version ORDER BY date DESC) AS rn
    FROM sig
    WHERE `signal` != 'Hold'
)
SELECT
    stock,
    version,
    date AS last_signal_date,
    `signal` AS last_signal
FROM ranked_signals
WHERE rn = 1
ORDER BY stock, version;
