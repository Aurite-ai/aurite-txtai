# Set shell to bash
set shell := ["bash", "-c"]

# Load .env file if it exists
set dotenv-load := true

# Default recipe (runs when you type 'just')
default:
    @just --list

# Development setup and management
setup:
    #!/usr/bin/env bash
    # Check if virtual environment is activated
    if [[ -z "${VIRTUAL_ENV}" ]]; then
        echo "Virtual environment not activated. Please run 'source .venv/bin/activate' first"
        exit 1
    fi

    echo "Setting up development environment..."

    # Install system dependencies
    sudo apt-get update
    sudo apt-get install -y python3-dev libpq-dev build-essential postgresql postgresql-contrib
    pip install --upgrade pip
    pip install pip-tools

    # Install pre-commit without mypy hook
    pip install pre-commit
    pre-commit install --hook-type pre-push

    echo "Setup complete!"

pip-install:
    #!/usr/bin/env bash
    pip install --upgrade pip
    pip install pip-tools
    pip-compile requirements.in
    pip install -r requirements.txt

# Database commands
db-setup:
    #!/usr/bin/env bash
    set -e  # Exit on error
    echo "Setting up database configuration..."

    # Create PostgreSQL user if it doesn't exist
    if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='aurite_user'" | grep -q 1; then
        echo "Creating PostgreSQL user: aurite_user"
        sudo -u postgres psql -c "CREATE USER aurite_user WITH PASSWORD 'autumnBank36' CREATEDB;"
    fi

    # Grant schema permissions for each database
    for DB in aurite_db aurite_test_db; do
        # Create database if it doesn't exist
        if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB; then
            echo "Creating database: $DB"
            sudo -u postgres createdb -O aurite_user $DB
        fi

        # Set up permissions using individual commands instead of heredoc
        echo "Setting up permissions for $DB..."
        sudo -u postgres psql -d $DB -c "GRANT ALL ON SCHEMA public TO aurite_user;"
        sudo -u postgres psql -d $DB -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO aurite_user;"
        sudo -u postgres psql -d $DB -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO aurite_user;"
        sudo -u postgres psql -d $DB -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO aurite_user;"
    done

    # Initialize schema for both databases
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

db-init:
    bash scripts/init_db.sh

db-reset:
    #!/usr/bin/env bash
    echo "Resetting databases..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        dropdb aurite_db --if-exists
        dropdb aurite_test_db --if-exists
    else
        sudo -u postgres dropdb aurite_db --if-exists
        sudo -u postgres dropdb aurite_test_db --if-exists
    fi
    just db-setup

db-migrate:
    alembic upgrade head

db-test:
    python3 -m pytest tests/unit/services/db/test_operations.py -v

# Testing commands
test:
    python3 -m pytest tests/ -v

test-db:
    python3 -m pytest tests/unit/services/db -v

test-api:
    python3 -m pytest tests/integration/api -v

# Development server
dev:
    uvicorn aurite_txtai.main:app --reload --host 0.0.0.0 --port 8080

# Other commands remain unchanged...

# Cleanup
clean:
    rm -rf __pycache__ .pytest_cache .coverage .venv build dist *.egg-info
    find . -type d -name "__pycache__" -exec rm -r {} +

# Git shortcuts
git-acp message:
    git add .
    git commit -m "{{message}}"
    git push

# Utility
requirements:
    pip-compile requirements.in
    pip-compile requirements.dev.in
