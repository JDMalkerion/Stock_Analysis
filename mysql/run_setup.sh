#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DATA_DIR="${PROJECT_ROOT}/data"
ENV_FILE="${SCRIPT_DIR}/.env"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "Error: $ENV_FILE not found" >&2
    exit 1
fi

set -a
source "$ENV_FILE"
set +a

DB_NAME="${1:-${MYSQL_DATABASE:-stock_analysis}}"

echo "Setting up tables and loading data into database '$DB_NAME'..."

# Create a temporary SQL file with __DATA_DIR__ replaced
TMP_SQL=$(mktemp)
trap 'rm -f "$TMP_SQL"' EXIT

sed "s|__DATA_DIR__|${DATA_DIR}|g" "${SCRIPT_DIR}/00_setup.sql" > "$TMP_SQL"

# Run the SQL script through mysql_cli.sh
OUTPUT=$("${SCRIPT_DIR}/mysql_cli.sh" "$DB_NAME" < "$TMP_SQL")

# Check if there were any warnings output by SHOW WARNINGS
if echo "$OUTPUT" | grep -iE 'Warning|Error' >/dev/null; then
    echo "Warnings or errors encountered during data load:" >&2
    echo "$OUTPUT" >&2
    exit 1
fi

echo "Data loaded successfully with zero warnings!"
