WITH adjusted AS (
    SELECT
        'TCS' AS stock,
        date,
        CASE
            WHEN date < '2018-05-31' THEN close_price / 2.0
            ELSE close_price
        END AS adj_close
    FROM tcs
    UNION ALL
    SELECT
        'Infosys' AS stock,
        date,
        CASE
            WHEN date < '2015-06-15' THEN close_price / 2.0
            ELSE close_price
        END AS adj_close
    FROM infosys
)
SELECT
    stock,
    ROUND(
        100.0 * (
            MAX(CASE WHEN date = '2018-07-31' THEN adj_close END) -
            MAX(CASE WHEN date = '2015-01-01' THEN adj_close END)
        ) / MAX(CASE WHEN date = '2015-01-01' THEN adj_close END),
        1
    ) AS adjusted_pct_change
FROM adjusted
GROUP BY stock
ORDER BY stock;
