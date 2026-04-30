#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}

while ! nc -z $DB_HOST $DB_PORT; do
  echo "Database not ready, waiting..."
  sleep 1
done
echo "Database is ready!"

# In a real app we would run migrations here:
# alembic upgrade head

# Start the server
echo "Starting FastAPI server..."
# Using uvicorn as the ASGI server. We specify app.main:app because of the project structure
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload