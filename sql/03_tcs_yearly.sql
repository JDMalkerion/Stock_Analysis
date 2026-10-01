SELECT
    strftime('%Y', date) AS year,
    ROUND(AVG(close_price), 2) AS avg_close_price
FROM tcs
GROUP BY strftime('%Y', date)
ORDER BY year ASC;
