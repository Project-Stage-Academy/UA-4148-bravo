#!/bin/bash
set -euo pipefail

# Function to validate database/user name (allow only a-z, A-Z, 0-9, and _)
function is_valid_name() {
  local name="$1"
  if [[ "$name" =~ ^[a-zA-Z0-9_]+$ ]]; then
    return 0
  else
    return 1
  fi
}

function create_user_and_database() {
  local database="$1"

  # Validate name
  if ! is_valid_name "$database"; then
    echo "Error: database/user name '$database' contains invalid characters."
    exit 1
  fi

  echo "Creating user and database '$database' if they do not exist"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    DO
    \$\$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$database') THEN
        EXECUTE format('CREATE USER %I;', '$database');
      END IF;

      IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$database') THEN
        EXECUTE format('CREATE DATABASE %I;', '$database');
      END IF;

      EXECUTE format('GRANT ALL PRIVILEGES ON DATABASE %I TO %I;', '$database', '$database');
    END
    \$\$
    ;
EOSQL
}

if [ -n "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
  echo "Multiple databases requested: $POSTGRES_MULTIPLE_DATABASES"
  IFS=',' read -ra DBS <<< "$POSTGRES_MULTIPLE_DATABASES"
  for db in "${DBS[@]}"; do
    create_user_and_database "$db"
  done
fi
