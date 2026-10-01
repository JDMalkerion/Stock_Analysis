-- Rebuild TCS signals for both raw close_price and adjusted adj_close
-- Section 1: Summary of Buy and Sell counts for each version
WITH tcs_series AS (
    SELECT
        'raw' AS version,
        date,
        close_price
    FROM tcs
    UNION ALL
    SELECT
        'adjusted' AS version,
        date,
        CASE
            WHEN date < '2018-05-31' THEN close_price / 2.0
            ELSE close_price
        END AS close_price
    FROM tcs
),
ma AS (
    SELECT
        version,
        date,
        close_price,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY version ORDER BY date) >= 20
            THEN ROUND(AVG(close_price) OVER (PARTITION BY version ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 2)
            ELSE NULL
        END AS ma20,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY version ORDER BY date) >= 50
            THEN ROUND(AVG(close_price) OVER (PARTITION BY version ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW), 2)
            ELSE NULL
        END AS ma50
    FROM tcs_series
),
lagged AS (
    SELECT
        version,
        date,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (PARTITION BY version ORDER BY date) AS prev_ma20,
        LAG(ma50) OVER (PARTITION BY version ORDER BY date) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT
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
    version,
    SUM(CASE WHEN `signal` = 'Buy' THEN 1 ELSE 0 END) AS buys,
    SUM(CASE WHEN `signal` = 'Sell' THEN 1 ELSE 0 END) AS sells
FROM sig
GROUP BY version
ORDER BY version;

-- Section 2: Dates with signals that differ between raw and adjusted versions
WITH tcs_series AS (
    SELECT
        'raw' AS version,
        date,
        close_price
    FROM tcs
    UNION ALL
    SELECT
        'adjusted' AS version,
        date,
        CASE
            WHEN date < '2018-05-31' THEN close_price / 2.0
            ELSE close_price
        END AS close_price
    FROM tcs
),
ma AS (
    SELECT
        version,
        date,
        close_price,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY version ORDER BY date) >= 20
            THEN ROUND(AVG(close_price) OVER (PARTITION BY version ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 2)
            ELSE NULL
        END AS ma20,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY version ORDER BY date) >= 50
            THEN ROUND(AVG(close_price) OVER (PARTITION BY version ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW), 2)
            ELSE NULL
        END AS ma50
    FROM tcs_series
),
lagged AS (
    SELECT
        version,
        date,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (PARTITION BY version ORDER BY date) AS prev_ma20,
        LAG(ma50) OVER (PARTITION BY version ORDER BY date) AS prev_ma50
    FROM ma
),
sig AS (
    SELECT
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
    r.date,
    r.`signal` AS raw_signal,
    a.`signal` AS adj_signal
FROM (SELECT date, `signal` FROM sig WHERE version = 'raw') r
JOIN (SELECT date, `signal` FROM sig WHERE version = 'adjusted') a ON r.date = a.date
WHERE r.`signal` != a.`signal`
ORDER BY r.date;
