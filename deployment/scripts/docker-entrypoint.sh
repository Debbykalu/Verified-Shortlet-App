#!/bin/sh
set -e

echo "Running database migrations..."

flask db upgrade || exit 1

echo "Starting Gunicorn..."

exec gunicorn \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --threads 4 \
    starter:app