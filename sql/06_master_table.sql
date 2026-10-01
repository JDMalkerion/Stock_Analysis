DROP TABLE IF EXISTS master_table;
CREATE TABLE master_table AS
SELECT
    b.date,
    b.close_price AS bajaj,
    tcs.close_price AS tcs,
    tvs.close_price AS tvs,
    inf.close_price AS infosys,
    eic.close_price AS eicher,
    her.close_price AS hero
FROM bajaj_auto b
JOIN tcs ON b.date = tcs.date
JOIN tvs_motors tvs ON b.date = tvs.date
JOIN infosys inf ON b.date = inf.date
JOIN eicher_motors eic ON b.date = eic.date
JOIN hero_motocorp her ON b.date = her.date
ORDER BY b.date;
