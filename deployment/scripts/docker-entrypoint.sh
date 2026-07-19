#!/bin/sh
set -e

echo "Running database migrations..."

export FLASK_APP=starter.py

flask db upgrade

echo "Starting Gunicorn..."

exec gunicorn \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --threads 4 \
    starter:app