#!/bin/bash

echo "Waiting for database..."
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}

if command -v nc >/dev/null 2>&1; then
  while ! nc -z $DB_HOST $DB_PORT; do
    echo "Database not ready, waiting..."
    sleep 1
  done
else
  echo "nc not found, sleeping for 5s..."
  sleep 5
fi

echo "Database is ready!"

# echo "Running migrations..."
# python manage.py migrate --noinput

# echo "Collecting static files..."
# python manage.py collectstatic --noinput

echo "Starting Django development server..."

exec python manage.py runserver 0.0.0.0:8000
