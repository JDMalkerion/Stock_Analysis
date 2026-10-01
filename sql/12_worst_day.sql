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
daily AS (
    SELECT
        stock,
        date,
        close_price,
        LAG(close_price) OVER (PARTITION BY stock ORDER BY date) AS prev_close
    FROM prices
),
moves AS (
    SELECT
        stock,
        date,
        close_price,
        ROUND(100.0 * (close_price / prev_close - 1), 1) AS pct_move
    FROM daily
    WHERE prev_close IS NOT NULL
),
ranked AS (
    SELECT
        stock,
        date,
        close_price,
        pct_move,
        ROW_NUMBER() OVER (PARTITION BY stock ORDER BY pct_move ASC) AS rn
    FROM moves
)
SELECT
    stock,
    date,
    close_price,
    pct_move
FROM ranked
WHERE rn = 1
ORDER BY pct_move ASC;
