#!/usr/bin/env bash
# build_submission.sh – regenerates submission/stock_market_analysis.txt from
# mysql/00_setup.sql and mysql/stock_analysis.sql so they cannot drift apart.
# Usage: bash mysql/build_submission.sh (from project root)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUT="${PROJECT_ROOT}/submission/stock_market_analysis.txt"

mkdir -p "${PROJECT_ROOT}/submission"

cat > "$OUT" << 'HEADER'
-- ==============================================================================
-- Project       : Stock Market Analysis – MySQL 8 Submission
-- Requirements  : MySQL 8.0 or newer with local_infile enabled
-- How to run    :
--   Option A (command line):
--     mysql --local-infile=1 -u root -p < stock_market_analysis.txt
--   Option B (MySQL Workbench):
--     Open the file and click the lightning-bolt run icon.
--     Make sure the server has SET GLOBAL local_infile = 1; applied first.
-- Server setup  : Run once as root before executing this file:
--     SET GLOBAL local_infile = 1;
-- *** ONE THING TO EDIT ***
--   In the six LOAD DATA statements below, replace /PATH/TO/CSV/ with
--   the absolute path to the folder containing the six CSV files,
--   keeping the trailing slash. Example:
--     /home/user/projects/Stock_Analysis/data/
-- ==============================================================================

-- ---------------------------------------------------------------------------
-- Database
-- ---------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS stock_analysis;
USE stock_analysis;

HEADER

# Append setup SQL with data-path placeholder substituted
sed 's|__DATA_DIR__|/PATH/TO/CSV|g' "${SCRIPT_DIR}/00_setup.sql" >> "$OUT"

echo "" >> "$OUT"

# Append full analysis SQL, unchanged
cat "${SCRIPT_DIR}/stock_analysis.sql" >> "$OUT"

echo "Built: $OUT  ($(wc -l < "$OUT") lines)"
