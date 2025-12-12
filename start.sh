#!/bin/bash
set -e

# Get PORT from environment, default to 8080
PORT=${PORT:-8080}

echo "========================================="
echo "Starting WorkBoard API"
echo "========================================="
echo "Port: $PORT"
echo "Database: ${DATABASE_URL:0:30}..."
echo "CORS Origins: $CORS_ORIGINS"
echo "========================================="

# Start uvicorn with explicit port
exec uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info
