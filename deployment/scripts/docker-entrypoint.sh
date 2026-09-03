#!/bin/sh
set -e

echo "=================================="
echo "Verified Shortlet Starting"
echo "=================================="

export FLASK_APP=starter.py

echo "Waiting for MySQL database connection..."
python -c "
import time, os
from sqlalchemy import create_engine

uri = os.getenv('SQLALCHEMY_DATABASE_URI')
if not uri:
    user = os.getenv('MYSQL_USER', 'appuser')
    password = os.getenv('MYSQL_PASSWORD', 'appuserpass')
    host = os.getenv('MYSQL_HOST', 'mysql')
    port = os.getenv('MYSQL_PORT', '3306')
    db = os.getenv('MYSQL_DATABASE', 'shortletdb')
    uri = f'mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db}'

engine = create_engine(uri)
connected = False
for i in range(30):
    try:
        with engine.connect() as conn:
            print('Successfully connected to MySQL database!')
            connected = True
            break
    except Exception as e:
        print(f'Waiting for MySQL ({i+1}/30)... {e}')
        time.sleep(2)

if not connected:
    raise Exception('Could not connect to MySQL database after 60 seconds.')
"

echo "Ensuring database schema exists..."
python -c "
from starter import app
from pkg.models import db
with app.app_context():
    db.create_all()
    print('Schema check / creation complete.')
"

echo "Applying database migrations..."
flask db upgrade || {
    echo "Migration note: Stamping head revision..."
    flask db stamp head
}

echo "Starting Gunicorn..."
exec gunicorn \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --threads 4 \
    starter:app