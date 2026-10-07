#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "Error: $ENV_FILE not found" >&2
    exit 1
fi

set -a
source "$ENV_FILE"
set +a

CONTAINER_NAME="stocks-mysql"
VOLUME_NAME="stocks-mysql-data"
IMAGE="docker.io/library/mysql:8.4"

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"

# Check if container exists
if distrobox-host-exec podman container exists "$CONTAINER_NAME" 2>/dev/null; then
    STATUS=$(distrobox-host-exec podman inspect --format '{{.State.Status}}' "$CONTAINER_NAME")
    if [[ "$STATUS" != "running" ]]; then
        echo "Starting existing container $CONTAINER_NAME..."
        distrobox-host-exec podman start "$CONTAINER_NAME"
    else
        echo "Container $CONTAINER_NAME is already running."
    fi
else
    echo "Creating and starting container $CONTAINER_NAME..."
    distrobox-host-exec podman run -d \
        --name "$CONTAINER_NAME" \
        -v "${VOLUME_NAME}:/var/lib/mysql" \
        -p 127.0.0.1:3306:3306 \
        --env-file "$ENV_FILE" \
        "$IMAGE" \
        --local-infile=1
fi

echo "Waiting for MySQL to become ready with mysqladmin ping loop..."
READY=0
for i in $(seq 1 60); do
    STATUS=$(distrobox-host-exec podman inspect --format '{{.State.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "unknown")
    if [[ "$STATUS" == "exited" || "$STATUS" == "dead" ]]; then
        echo "Container $CONTAINER_NAME stopped unexpectedly with status: $STATUS" >&2
        distrobox-host-exec podman logs --tail 30 "$CONTAINER_NAME" >&2
        exit 1
    fi

    if MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqladmin ping -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" --silent 2>/dev/null; then
        READY=1
        echo "MySQL is ready! (Attempt $i)"
        break
    fi

    echo "Attempt $i/60: MySQL not ready yet - sleeping 2s..."
    sleep 2
done

if [[ "$READY" -ne 1 ]]; then
    echo "MySQL failed to become ready within 120 seconds." >&2
    distrobox-host-exec podman logs --tail 30 "$CONTAINER_NAME" >&2
    exit 1
fi
