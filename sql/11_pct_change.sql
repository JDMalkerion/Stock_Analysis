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
ends AS (
    SELECT
        stock,
        MIN(date) AS first_date,
        MAX(date) AS last_date
    FROM prices
    GROUP BY stock
)
SELECT
    e.stock,
    p_first.close_price AS first_close,
    p_last.close_price AS last_close,
    ROUND(100.0 * (p_last.close_price - p_first.close_price) / p_first.close_price, 1) AS pct_change
FROM ends e
JOIN prices p_first ON e.stock = p_first.stock AND e.first_date = p_first.date
JOIN prices p_last ON e.stock = p_last.stock AND e.last_date = p_last.date
ORDER BY pct_change DESC;
