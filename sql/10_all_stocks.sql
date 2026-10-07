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
