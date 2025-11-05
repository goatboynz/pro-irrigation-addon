#!/usr/bin/env bash
set -e

echo "============================================================"
echo "Pro-Irrigation Add-on - Startup Script"
echo "============================================================"

# Read configuration from Home Assistant options
CONFIG_PATH=/data/options.json

if [ -f "$CONFIG_PATH" ]; then
    LOG_LEVEL=$(jq -r '.log_level // "info"' $CONFIG_PATH)
else
    LOG_LEVEL="${LOG_LEVEL:-info}"
fi

# Set default number of workers (1 for single-threaded operation)
# Multiple workers would require shared state management for scheduler/queue
WORKERS="${WORKERS:-1}"

# Database path
DATABASE_PATH="${DATABASE_PATH:-/data/irrigation.db}"

echo "Configuration:"
echo "  Log level: $LOG_LEVEL"
echo "  Workers: $WORKERS"
echo "  Database path: $DATABASE_PATH"
echo "  Port: 8000"
echo "============================================================"

# Verify data directory exists and is writable
if [ ! -d "/data" ]; then
    echo "ERROR: /data directory does not exist"
    exit 1
fi

if [ ! -w "/data" ]; then
    echo "ERROR: /data directory is not writable"
    exit 1
fi

# Change to application directory
cd /app

# Check if database exists
if [ -f "$DATABASE_PATH" ]; then
    echo "Database found at $DATABASE_PATH"
else
    echo "Database will be created at $DATABASE_PATH"
fi

# Start the FastAPI backend server with uvicorn
# The backend serves both the API and the static frontend files
# Using single worker to ensure scheduler and queue processor run in one process
echo "Starting FastAPI server..."
echo "============================================================"

exec python -m uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "$WORKERS" \
    --log-level "$LOG_LEVEL" \
    --no-access-log \
    --proxy-headers \
    --forwarded-allow-ips '*'
