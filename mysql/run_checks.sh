#!/usr/bin/env bash
# run_checks.sh – Ensures the MySQL container is running, then executes
# verify_checkpoints.py and verify_parity.py against the given database.
#
# Usage (from project root):
#   bash mysql/run_checks.sh [db_name]
#   bash mysql/run_checks.sh stock_analysis_scratch
#
# Why this wrapper? The two Python checkers connect to MySQL directly via
# pymysql. When MySQL is not running (e.g. fresh terminal, after a reboot),
# they crash with:
#   pymysql.err.OperationalError: (2003, "Can't connect to MySQL server
#   on '127.0.0.1' ([Errno 111] Connection refused)")
# This wrapper brings the container up first, then runs both scripts.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_NAME="${1:-stock_analysis}"

echo "=== Ensuring MySQL container is up ==="
bash "${SCRIPT_DIR}/db_up.sh"

echo ""
echo "=== Running verify_checkpoints.py (db: ${DB_NAME}) ==="
python3 "${SCRIPT_DIR}/verify_checkpoints.py" "${DB_NAME}"

echo ""
echo "=== Running verify_parity.py (db: ${DB_NAME}) ==="
python3 "${SCRIPT_DIR}/verify_parity.py" "${DB_NAME}"
