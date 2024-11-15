#!/bin/bash
set -e

echo "Starting database setup..."

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS setup
    if ! psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='aurite_user'" | grep -q 1; then
        echo "Setting up PostgreSQL user and database..."
        psql postgres << EOF
CREATE USER aurite_user WITH PASSWORD 'autumnBank36';
CREATE DATABASE aurite_db OWNER aurite_user;
CREATE DATABASE aurite_test_db OWNER aurite_user;
\q
EOF
    else
        echo "PostgreSQL user 'aurite_user' already exists."
    fi

else
    # Linux setup
    echo "Setting up PostgreSQL user and databases..."
    sudo -u postgres psql << EOF
DROP DATABASE IF EXISTS aurite_db;
DROP DATABASE IF EXISTS aurite_test_db;
DROP USER IF EXISTS aurite_user;
CREATE USER aurite_user WITH PASSWORD 'autumnBank36';
ALTER USER aurite_user CREATEDB;
\q
EOF

    # Create databases
    echo "Creating databases..."
    sudo -u postgres createdb aurite_db
    sudo -u postgres createdb aurite_test_db

    # Grant database ownership
    echo "Granting database privileges..."
    sudo -u postgres psql << EOF
GRANT ALL PRIVILEGES ON DATABASE aurite_db TO aurite_user;
GRANT ALL PRIVILEGES ON DATABASE aurite_test_db TO aurite_user;
\q
EOF

    # Grant schema permissions for each database
    for DB in aurite_db aurite_test_db; do
        echo "Setting up permissions for $DB..."
        sudo -u postgres psql -d $DB << EOF
GRANT ALL ON SCHEMA public TO aurite_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO aurite_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO aurite_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO aurite_user;
\q
EOF
    done

    # Initialize schema for both databases
    export PGPASSWORD='autumnBank36'
    for DB in aurite_db aurite_test_db; do
        echo "Initializing schema for $DB..."
        if ! psql -h localhost -U aurite_user -d $DB -c "SELECT 1 FROM pg_type WHERE typname = 'domain'" &> /dev/null; then
            psql -h localhost -U aurite_user -d $DB -f src/services/db/schema.sql
            echo "Schema initialized for $DB"
        else
            echo "Schema already exists in $DB"
        fi
    done
fi

echo "Database setup complete!"
