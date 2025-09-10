#!/bin/sh
set -eu

# ------------------------------
# Configuration
# ------------------------------
db_host="${DB_HOST:?Error: DB_HOST is not set}"
db_port="${DB_PORT:-5432}"
max_retries="${MAX_RETRIES:-30}"
sleep_duration="${SLEEP_DURATION:-2}"
count=0

# ------------------------------
# Wait for PostgreSQL
# ------------------------------
echo "Waiting for PostgreSQL to be ready at $db_host:$db_port..."

while ! pg_isready -h "$db_host" -p "$db_port" > /dev/null 2>&1; do
  count=$((count + 1))
  echo "Waiting for PostgreSQL at $db_host:$db_port... (attempt $count)"
  if [ "$max_retries" -gt 0 ] && [ "$count" -ge "$max_retries" ]; then
    echo "PostgreSQL is still not available after $max_retries attempts, exiting."
    exit 1
  fi
  sleep "$sleep_duration"
done

echo "PostgreSQL is ready - continuing..."

# ------------------------------
# Django setup
# ------------------------------
export DJANGO_SETTINGS_MODULE=core.settings
python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

# ------------------------------
# Execute the passed command, or default to gunicorn
# ------------------------------
if [ "$#" -eq 0 ]; then
  echo "No command provided, defaulting to 'gunicorn core.wsgi:application'"
  exec gunicorn core.wsgi:application --bind=0.0.0.0:8000 --workers=3 --timeout=120
else
  exec "$@"
fi





