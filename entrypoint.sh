#!/bin/sh
set -eu

# Checking for host as first argument
if [ -z "${1:-}" ]; then
  echo "Usage: $0 <host> [command...]"
  exit 1
fi

host="$1"
shift

port="${DB_PORT:-5432}"

# Maximum number of attempts (0 = wait indefinitely)
max_retries=30
count=0

echo "Waiting for PostgreSQL to be ready at $host:$port..."

while ! pg_isready -h "$host" -p "$port" > /dev/null 2>&1; do
  count=$((count + 1))
  echo "Waiting for PostgreSQL at $host:$port... (attempt $count)"
  if [ "$max_retries" -gt 0 ] && [ "$count" -ge "$max_retries" ]; then
    echo "PostgreSQL is still not available after $max_retries attempts, exiting."
    exit 1
  fi
  sleep 2
done

echo "PostgreSQL is ready - continuing..."

python manage.py migrate
python manage.py collectstatic --noinput

exec "$@"
