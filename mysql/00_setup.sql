-- Setup script for Stock Analysis MySQL database
-- Recreates the six raw stock price tables and loads data from CSVs.

-- 1. bajaj_auto
DROP TABLE IF EXISTS bajaj_auto;
CREATE TABLE bajaj_auto (
    date DATE,
    open_price DOUBLE,
    high_price DOUBLE,
    low_price DOUBLE,
    close_price DOUBLE,
    wap DOUBLE,
    no_of_shares BIGINT,
    no_of_trades INT,
    total_turnover DOUBLE,
    deliverable_qty BIGINT,
    pct_deli_qty DOUBLE,
    spread_high_low DOUBLE,
    spread_close_open DOUBLE
);
LOAD DATA LOCAL INFILE '__DATA_DIR__/Bajaj Auto.csv'
INTO TABLE bajaj_auto
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@d, @op, @hp, @lp, @cp, @wap, @nos, @not, @tt, @dq, @pdq, @shl, @sco)
SET
    date = STR_TO_DATE(NULLIF(@d, ''), '%d-%M-%Y'),
    open_price = NULLIF(@op, ''),
    high_price = NULLIF(@hp, ''),
    low_price = NULLIF(@lp, ''),
    close_price = NULLIF(@cp, ''),
    wap = NULLIF(@wap, ''),
    no_of_shares = NULLIF(@nos, ''),
    no_of_trades = NULLIF(@not, ''),
    total_turnover = NULLIF(@tt, ''),
    deliverable_qty = NULLIF(@dq, ''),
    pct_deli_qty = NULLIF(@pdq, ''),
    spread_high_low = NULLIF(@shl, ''),
    spread_close_open = NULLIF(TRIM(@sco), '');
SHOW WARNINGS;

-- 2. eicher_motors
DROP TABLE IF EXISTS eicher_motors;
CREATE TABLE eicher_motors (
    date DATE,
    open_price DOUBLE,
    high_price DOUBLE,
    low_price DOUBLE,
    close_price DOUBLE,
    wap DOUBLE,
    no_of_shares BIGINT,
    no_of_trades INT,
    total_turnover DOUBLE,
    deliverable_qty BIGINT,
    pct_deli_qty DOUBLE,
    spread_high_low DOUBLE,
    spread_close_open DOUBLE
);
LOAD DATA LOCAL INFILE '__DATA_DIR__/Eicher Motors.csv'
INTO TABLE eicher_motors
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@d, @op, @hp, @lp, @cp, @wap, @nos, @not, @tt, @dq, @pdq, @shl, @sco)
SET
    date = STR_TO_DATE(NULLIF(@d, ''), '%d-%M-%Y'),
    open_price = NULLIF(@op, ''),
    high_price = NULLIF(@hp, ''),
    low_price = NULLIF(@lp, ''),
    close_price = NULLIF(@cp, ''),
    wap = NULLIF(@wap, ''),
    no_of_shares = NULLIF(@nos, ''),
    no_of_trades = NULLIF(@not, ''),
    total_turnover = NULLIF(@tt, ''),
    deliverable_qty = NULLIF(@dq, ''),
    pct_deli_qty = NULLIF(@pdq, ''),
    spread_high_low = NULLIF(@shl, ''),
    spread_close_open = NULLIF(TRIM(@sco), '');
SHOW WARNINGS;

-- 3. hero_motocorp
DROP TABLE IF EXISTS hero_motocorp;
CREATE TABLE hero_motocorp (
    date DATE,
    open_price DOUBLE,
    high_price DOUBLE,
    low_price DOUBLE,
    close_price DOUBLE,
    wap DOUBLE,
    no_of_shares BIGINT,
    no_of_trades INT,
    total_turnover DOUBLE,
    deliverable_qty BIGINT,
    pct_deli_qty DOUBLE,
    spread_high_low DOUBLE,
    spread_close_open DOUBLE
);
LOAD DATA LOCAL INFILE '__DATA_DIR__/Hero Motocorp.csv'
INTO TABLE hero_motocorp
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@d, @op, @hp, @lp, @cp, @wap, @nos, @not, @tt, @dq, @pdq, @shl, @sco)
SET
    date = STR_TO_DATE(NULLIF(@d, ''), '%d-%M-%Y'),
    open_price = NULLIF(@op, ''),
    high_price = NULLIF(@hp, ''),
    low_price = NULLIF(@lp, ''),
    close_price = NULLIF(@cp, ''),
    wap = NULLIF(@wap, ''),
    no_of_shares = NULLIF(@nos, ''),
    no_of_trades = NULLIF(@not, ''),
    total_turnover = NULLIF(@tt, ''),
    deliverable_qty = NULLIF(@dq, ''),
    pct_deli_qty = NULLIF(@pdq, ''),
    spread_high_low = NULLIF(@shl, ''),
    spread_close_open = NULLIF(TRIM(@sco), '');
SHOW WARNINGS;

-- 4. infosys
DROP TABLE IF EXISTS infosys;
CREATE TABLE infosys (
    date DATE,
    open_price DOUBLE,
    high_price DOUBLE,
    low_price DOUBLE,
    close_price DOUBLE,
    wap DOUBLE,
    no_of_shares BIGINT,
    no_of_trades INT,
    total_turnover DOUBLE,
    deliverable_qty BIGINT,
    pct_deli_qty DOUBLE,
    spread_high_low DOUBLE,
    spread_close_open DOUBLE
);
LOAD DATA LOCAL INFILE '__DATA_DIR__/Infosys.csv'
INTO TABLE infosys
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@d, @op, @hp, @lp, @cp, @wap, @nos, @not, @tt, @dq, @pdq, @shl, @sco)
SET
    date = STR_TO_DATE(NULLIF(@d, ''), '%d-%M-%Y'),
    open_price = NULLIF(@op, ''),
    high_price = NULLIF(@hp, ''),
    low_price = NULLIF(@lp, ''),
    close_price = NULLIF(@cp, ''),
    wap = NULLIF(@wap, ''),
    no_of_shares = NULLIF(@nos, ''),
    no_of_trades = NULLIF(@not, ''),
    total_turnover = NULLIF(@tt, ''),
    deliverable_qty = NULLIF(@dq, ''),
    pct_deli_qty = NULLIF(@pdq, ''),
    spread_high_low = NULLIF(@shl, ''),
    spread_close_open = NULLIF(TRIM(@sco), '');
SHOW WARNINGS;

-- 5. tcs
DROP TABLE IF EXISTS tcs;
CREATE TABLE tcs (
    date DATE,
    open_price DOUBLE,
    high_price DOUBLE,
    low_price DOUBLE,
    close_price DOUBLE,
    wap DOUBLE,
    no_of_shares BIGINT,
    no_of_trades INT,
    total_turnover DOUBLE,
    deliverable_qty BIGINT,
    pct_deli_qty DOUBLE,
    spread_high_low DOUBLE,
    spread_close_open DOUBLE
);
LOAD DATA LOCAL INFILE '__DATA_DIR__/TCS.csv'
INTO TABLE tcs
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@d, @op, @hp, @lp, @cp, @wap, @nos, @not, @tt, @dq, @pdq, @shl, @sco)
SET
    date = STR_TO_DATE(NULLIF(@d, ''), '%d-%M-%Y'),
    open_price = NULLIF(@op, ''),
    high_price = NULLIF(@hp, ''),
    low_price = NULLIF(@lp, ''),
    close_price = NULLIF(@cp, ''),
    wap = NULLIF(@wap, ''),
    no_of_shares = NULLIF(@nos, ''),
    no_of_trades = NULLIF(@not, ''),
    total_turnover = NULLIF(@tt, ''),
    deliverable_qty = NULLIF(@dq, ''),
    pct_deli_qty = NULLIF(@pdq, ''),
    spread_high_low = NULLIF(@shl, ''),
    spread_close_open = NULLIF(TRIM(@sco), '');
SHOW WARNINGS;

-- 6. tvs_motors
DROP TABLE IF EXISTS tvs_motors;
CREATE TABLE tvs_motors (
    date DATE,
    open_price DOUBLE,
    high_price DOUBLE,
    low_price DOUBLE,
    close_price DOUBLE,
    wap DOUBLE,
    no_of_shares BIGINT,
    no_of_trades INT,
    total_turnover DOUBLE,
    deliverable_qty BIGINT,
    pct_deli_qty DOUBLE,
    spread_high_low DOUBLE,
    spread_close_open DOUBLE
);
LOAD DATA LOCAL INFILE '__DATA_DIR__/TVS Motors.csv'
INTO TABLE tvs_motors
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@d, @op, @hp, @lp, @cp, @wap, @nos, @not, @tt, @dq, @pdq, @shl, @sco)
SET
    date = STR_TO_DATE(NULLIF(@d, ''), '%d-%M-%Y'),
    open_price = NULLIF(@op, ''),
    high_price = NULLIF(@hp, ''),
    low_price = NULLIF(@lp, ''),
    close_price = NULLIF(@cp, ''),
    wap = NULLIF(@wap, ''),
    no_of_shares = NULLIF(@nos, ''),
    no_of_trades = NULLIF(@not, ''),
    total_turnover = NULLIF(@tt, ''),
    deliverable_qty = NULLIF(@dq, ''),
    pct_deli_qty = NULLIF(@pdq, ''),
    spread_high_low = NULLIF(@shl, ''),
    spread_close_open = NULLIF(TRIM(@sco), '');
SHOW WARNINGS;
