-- Task 16: Whipsaw analysis on adjusted data for TCS/Infosys and raw for others

-- Section 1: Number of consecutive-signal pairs with a gap of 30 days or less per stock
WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto
    UNION ALL
    SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors
    UNION ALL
    SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp
    UNION ALL
    SELECT 'Infosys' AS stock, date, CASE WHEN date < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS close_price FROM infosys
    UNION ALL
    SELECT 'TCS' AS stock, date, CASE WHEN date < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS close_price FROM tcs
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
ledger AS (
    SELECT
        stock,
        date,
        `signal`,
        close_price,
        LAG(date) OVER (PARTITION BY stock ORDER BY date) AS prev_date,
        LAG(`signal`) OVER (PARTITION BY stock ORDER BY date) AS prev_signal,
        LAG(close_price) OVER (PARTITION BY stock ORDER BY date) AS prev_close,
        CAST(ROUND(julianday(date) - julianday(LAG(date) OVER (PARTITION BY stock ORDER BY date))) AS INTEGER) AS gap_days
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
    SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto
    UNION ALL
    SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors
    UNION ALL
    SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp
    UNION ALL
    SELECT 'Infosys' AS stock, date, CASE WHEN date < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS close_price FROM infosys
    UNION ALL
    SELECT 'TCS' AS stock, date, CASE WHEN date < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS close_price FROM tcs
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
ledger AS (
    SELECT
        stock,
        date,
        `signal`,
        close_price,
        LAG(date) OVER (PARTITION BY stock ORDER BY date) AS prev_date,
        LAG(`signal`) OVER (PARTITION BY stock ORDER BY date) AS prev_signal,
        LAG(close_price) OVER (PARTITION BY stock ORDER BY date) AS prev_close,
        CAST(ROUND(julianday(date) - julianday(LAG(date) OVER (PARTITION BY stock ORDER BY date))) AS INTEGER) AS gap_days
    FROM sig
    WHERE `signal` != 'Hold'
),
round_trips AS (
    SELECT
        stock,
        prev_date AS buy_date,
        date AS sell_date,
        prev_close AS buy_close,
        close_price AS sell_close,
        gap_days,
        ROUND(100.0 * (close_price - prev_close) / prev_close, 1) AS ret_pct
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
    SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto
    UNION ALL
    SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors
    UNION ALL
    SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp
    UNION ALL
    SELECT 'Infosys' AS stock, date, CASE WHEN date < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS close_price FROM infosys
    UNION ALL
    SELECT 'TCS' AS stock, date, CASE WHEN date < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS close_price FROM tcs
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
ledger AS (
    SELECT
        stock,
        date,
        `signal`,
        close_price,
        LAG(date) OVER (PARTITION BY stock ORDER BY date) AS prev_date,
        LAG(`signal`) OVER (PARTITION BY stock ORDER BY date) AS prev_signal,
        LAG(close_price) OVER (PARTITION BY stock ORDER BY date) AS prev_close,
        CAST(ROUND(julianday(date) - julianday(LAG(date) OVER (PARTITION BY stock ORDER BY date))) AS INTEGER) AS gap_days
    FROM sig
    WHERE `signal` != 'Hold'
)
SELECT
    stock,
    prev_date AS buy_date,
    date AS sell_date,
    prev_close AS buy_close,
    close_price AS sell_close,
    gap_days,
    ROUND(100.0 * (close_price - prev_close) / prev_close, 1) AS ret_pct
FROM ledger
WHERE prev_signal = 'Buy' AND `signal` = 'Sell'
ORDER BY stock, buy_date;

-- Section 4: Top 5 shortest-gap signal pairs across all stocks
WITH prices AS (
    SELECT 'Bajaj Auto' AS stock, date, close_price FROM bajaj_auto
    UNION ALL
    SELECT 'Eicher Motors' AS stock, date, close_price FROM eicher_motors
    UNION ALL
    SELECT 'Hero Motocorp' AS stock, date, close_price FROM hero_motocorp
    UNION ALL
    SELECT 'Infosys' AS stock, date, CASE WHEN date < '2015-06-15' THEN close_price / 2.0 ELSE close_price END AS close_price FROM infosys
    UNION ALL
    SELECT 'TCS' AS stock, date, CASE WHEN date < '2018-05-31' THEN close_price / 2.0 ELSE close_price END AS close_price FROM tcs
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
ledger AS (
    SELECT
        stock,
        prev_date,
        prev_signal,
        prev_close,
        date,
        `signal`,
        close_price,
        CAST(ROUND(julianday(date) - julianday(prev_date)) AS INTEGER) AS gap_days
    FROM (
        SELECT
            stock,
            date,
            `signal`,
            close_price,
            LAG(date) OVER (PARTITION BY stock ORDER BY date) AS prev_date,
            LAG(`signal`) OVER (PARTITION BY stock ORDER BY date) AS prev_signal,
            LAG(close_price) OVER (PARTITION BY stock ORDER BY date) AS prev_close
        FROM sig
        WHERE `signal` != 'Hold'
    )
    WHERE prev_date IS NOT NULL
)
SELECT
    stock,
    prev_date,
    prev_signal,
    prev_close,
    date,
    `signal`,
    close_price,
    gap_days
FROM ledger
ORDER BY gap_days ASC, stock ASC, prev_date ASC
LIMIT 5;
