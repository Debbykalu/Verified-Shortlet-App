#!/bin/sh
set -e

echo "=================================="
echo "Verified Shortlet Starting"
echo "=================================="

echo "Current directory:"
pwd

echo "Project files:"
ls -la

echo "Testing Flask import..."

python -c "from starter import app; print(app)"

echo "FLASK_APP=starter.py"

export FLASK_APP=starter.py

flask db upgrade || {
    echo "Warning: Database upgrade failed. Stamping migrations to head and retrying..."
    flask db stamp head
    flask db upgrade
}


echo "Starting Gunicorn..."

exec gunicorn \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --threads 4 \
    starter:app