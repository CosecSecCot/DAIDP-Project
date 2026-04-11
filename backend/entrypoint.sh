#!/bin/sh

echo "Waiting for database..."
until nc -z db 5432; do
  sleep 1
done

echo "Database is up!"

echo "Creating tables..."
python -m app.config.create_tables

echo "Seeding..."
python -m app.seed
echo "Seeded successfully!"

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000