#!/bin/bash

set -u

function create_database() {
	local database=$1 # receive below
	echo "  Creating database '$database' and schema '$POSTGRES_SCHEMA_NAME' "
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	    CREATE DATABASE $database;
	    GRANT ALL PRIVILEGES ON DATABASE $database TO $POSTGRES_USER;

	    \c $database;

	    GRANT ALL ON DATABASE $database TO $POSTGRES_USER;
      GRANT ALL ON SCHEMA $POSTGRES_SCHEMA_NAME TO $POSTGRES_USER;
      GRANT ALL ON ALL TABLES IN SCHEMA $POSTGRES_SCHEMA_NAME TO $POSTGRES_USER;
EOSQL

}

if [ -n "$POSTGRES_DB_NAME" ]; then
	echo "Database creation requested: $POSTGRES_DB_NAME"
	create_database "$POSTGRES_DB_NAME"
	echo "Database with table created"
fi