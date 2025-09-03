#!/bin/sh
set -eu

# ------------------------------
# Check for DB host argument
# ------------------------------
if [ -z "${1:-}" ]; then
  echo "Usage: $0 <db_host> [command...]"
  exit 1
fi

host="$1"
shift

port="${DB_PORT:-5432}"
max_retries="${MAX_RETRIES:-30}"     # default 30 retries
sleep_duration="${SLEEP_DURATION:-2}" # default 2 seconds
count=0

echo "Waiting for PostgreSQL to be ready at $host:$port..."

while ! pg_isready -h "$host" -p "$port" > /dev/null 2>&1; do
  count=$((count + 1))
  echo "Waiting for PostgreSQL at $host:$port... (attempt $count)"
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
# Run the passed command (Gunicorn)
# ------------------------------
exec "$@"

