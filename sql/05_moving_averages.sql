DROP TABLE IF EXISTS bajaj1;
CREATE TABLE bajaj1 AS
SELECT
    date,
    close_price,
    CASE
        WHEN ROW_NUMBER() OVER (ORDER BY date) >= 20
        THEN ROUND(AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 2)
        ELSE NULL
    END AS ma20,
    CASE
        WHEN ROW_NUMBER() OVER (ORDER BY date) >= 50
        THEN ROUND(AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW), 2)
        ELSE NULL
    END AS ma50
FROM bajaj_auto
ORDER BY date;
