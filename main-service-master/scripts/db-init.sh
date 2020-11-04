#!/bin/sh
set -u
set -o pipefail

# Function to execute SQL statement
execDBStatement() {
  PGPASSWORD=$WRITE_DB_PASS psql \
  --dbname=postgres \
  --username=$WRITE_DB_USER \
  --host=$WRITE_DB_HOST \
  --command="$1"
}

# Create Postgres Database
execDBStatement "CREATE DATABASE ${DB_NAME};"
execDBStatement "CREATE DATABASE ${DB_NAME}_test;"