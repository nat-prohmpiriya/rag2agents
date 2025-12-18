#!/bin/bash
set -e

# Create additional databases
# This script runs after the default database is created

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create litellm database for LiteLLM proxy
    CREATE DATABASE litellm;

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE litellm TO $POSTGRES_USER;
EOSQL

echo "Additional databases created successfully"
