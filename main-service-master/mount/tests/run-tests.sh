#!/bin/bash

set -e  # if any command fails, exit with an error

export UNIT_TEST=1

RUN_ALL="yes"
TEST=""
MARKS=""
SCRIPT_NAME=$0
DB_REBUILD="yes"
DB_MIGRATION="yes"
COVERAGE_MIN_LEVEL=30

while [[ $# -gt 0 ]]
do
  key="$1"

  case $key in
      -h|--help)
        echo "Usage: $SCRIPT_NAME filename"
        echo "    -o --only <test filename>: run only this filename,  can be used multiple times"
        echo "    -d --skip-db-rebuild: do not rebuild the DB"
        echo "    -m --skip-db-migration: do not run alembic"
        echo "    -h --help: display this message"
        exit 1
        shift
        ;;
      -o|--only)
        RUN_ALL="no"
        TEST="$TEST $2"
        shift # past argument
        shift # past value
        ;;
      -d|--skip-db-rebuild)
        DB_REBUILD="no"
        shift # past argument
        ;;
      -m|--skip-db-migration)
        DB_MIGRATION="no"
        shift # past argument
        ;;
      *)    # unknown option
        echo "Option: $key is unknown" # unknown option
        exit 1
        ;;
  esac
done

TEST_DB_NAME="${DB_NAME}_test"

if [[ "$DB_REBUILD" == "no" ]]; then
    echo "Skipping DB refresh -- don't do this often."
else
    echo "Refreshing Databases..."
    echo "Dropping ${TEST_DB_NAME}"
    echo "DROP DATABASE IF EXISTS ${TEST_DB_NAME}"|PGPASSWORD=$WRITE_DB_PASS psql -U $WRITE_DB_USER -h $WRITE_DB_HOST --dbname=postgres
    echo "Creating ${TEST_DB_NAME}"
    echo "CREATE DATABASE ${TEST_DB_NAME}"|PGPASSWORD=$WRITE_DB_PASS psql -U $WRITE_DB_USER -h $WRITE_DB_HOST --dbname=postgres
fi

if [[ "$DB_MIGRATION" == "yes" ]] ; then
    echo Running alembic migration
    alembic upgrade head
fi


echo Removing any lingering .pyc files
find . -name "*.pyc" -delete
export PYTHONDONTWRITEBYTECODE=1
cd tests/

if [[ "$RUN_ALL" == "yes" ]] ; then
      pytest \
        --junitxml=test_report.xml \
        --cov=app \
        --cov-report=html:htmlcov \
        --cov-report=xml:coverage_report.xml \
        --cov-report=term \
        --cov-fail-under=$COVERAGE_MIN_LEVEL
else
    pytest --flakes $MARKS $TESTS
fi
