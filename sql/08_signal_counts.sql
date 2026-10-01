SELECT
    `signal`,
    COUNT(*) AS count
FROM bajaj2
GROUP BY `signal`
ORDER BY `signal`;
