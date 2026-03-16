#!/bin/sh

set -e

echo "Running migrations..."
python manage.py migrate_schemas --shared
python manage.py migrate_schemas

echo "Starting application..."
exec "$@"
