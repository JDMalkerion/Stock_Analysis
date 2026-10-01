DROP TABLE IF EXISTS bajaj2;
CREATE TABLE bajaj2 AS
WITH t AS (
    SELECT
        date,
        close_price,
        ma20,
        ma50,
        LAG(ma20) OVER (ORDER BY date) AS prev_ma20,
        LAG(ma50) OVER (ORDER BY date) AS prev_ma50
    FROM bajaj1
)
SELECT
    date,
    close_price,
    CASE
        WHEN ma20 IS NULL OR ma50 IS NULL OR prev_ma20 IS NULL OR prev_ma50 IS NULL THEN 'Hold'
        WHEN ma20 > ma50 AND prev_ma20 <= prev_ma50 THEN 'Buy'
        WHEN ma20 < ma50 AND prev_ma20 >= prev_ma50 THEN 'Sell'
        ELSE 'Hold'
    END AS `signal`
FROM t
ORDER BY date;
