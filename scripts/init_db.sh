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
    if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='aurite_user'" | grep -q 1; then
        echo "Setting up PostgreSQL user and databases..."
        sudo -u postgres psql << EOF
DROP DATABASE IF EXISTS aurite_db;
DROP DATABASE IF EXISTS aurite_test_db;
DROP USER IF EXISTS aurite_user;
CREATE USER aurite_user WITH PASSWORD 'autumnBank36';
CREATE DATABASE aurite_db;
CREATE DATABASE aurite_test_db;
GRANT ALL PRIVILEGES ON DATABASE aurite_db TO aurite_user;
GRANT ALL PRIVILEGES ON DATABASE aurite_test_db TO aurite_user;
\q
EOF
    else
        echo "PostgreSQL user 'aurite_user' already exists."
    fi

    # Verify databases exist and recreate if needed
    for DB in aurite_db aurite_test_db; do
        if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB; then
            echo "Database not found, creating $DB..."
            sudo -u postgres psql << EOF
CREATE DATABASE $DB;
GRANT ALL PRIVILEGES ON DATABASE $DB TO aurite_user;
\q
EOF
        fi
    done
fi

# Initialize schema for both databases using password authentication
export PGPASSWORD='autumnBank36'
for DB in aurite_db aurite_test_db; do
    echo "Initializing schema for $DB..."
    if ! psql -h localhost -U aurite_user -d $DB -c "SELECT 1 FROM content" &> /dev/null; then
        psql -h localhost -U aurite_user -d $DB -f src/services/db/schema.sql
        echo "Schema initialized for $DB"
    else
        echo "Schema already exists in $DB"
    fi
done
unset PGPASSWORD

echo "Database setup complete!"
