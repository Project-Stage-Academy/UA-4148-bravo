#!/bin/sh
set -eu

# ------------------------------
# Check for DB host argument
# ------------------------------
if [ -z "${1:-}" ]; then
  echo "Usage: $0 <db_host> [command...]"
  exit 1
fi

db_host="$1"
shift  # Remove db_host from arguments

# ------------------------------
# Configuration
# ------------------------------
db_port="${DB_PORT:-5432}"
max_retries="${MAX_RETRIES:-30}"       # default 30 retries
sleep_duration="${SLEEP_DURATION:-2}"  # default 2 seconds
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
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# ------------------------------
# Execute the passed command, or default to gunicorn
# ------------------------------
if [ "$#" -eq 0 ]; then
  echo "No command provided, defaulting to 'gunicorn myproject.wsgi:application'"
  exec gunicorn myproject.wsgi:application
else
  exec "$@"
fi


