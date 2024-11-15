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
    echo "Setting up development environment..."
    sudo apt update
    sudo apt install postgresql postgresql-contrib
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install pip-tools build hatchling
    pip-compile requirements.in
    pip install -e .
    pip install -r requirements.txt
    pre-commit install
    echo "Setup complete! Run 'source .venv/bin/activate' to activate the environment"

# Database commands
db-setup:
    #!/usr/bin/env bash
    set -e  # Exit on error
    echo "Setting up databases..."
    
    # Ensure package is installed in development mode
    pip install -e .
    
    # Create PostgreSQL user if it doesn't exist
    if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='aurite_user'" | grep -q 1; then
        echo "Creating PostgreSQL user: aurite_user"
        sudo -u postgres psql -c "CREATE USER aurite_user WITH PASSWORD 'autumnBank36' CREATEDB;"
    fi
    
    # Modify authentication method in pg_hba.conf
    if ! sudo grep -q "local.*all.*aurite_user.*md5" /etc/postgresql/*/main/pg_hba.conf; then
        echo "Updating PostgreSQL authentication configuration..."
        echo "local   all             aurite_user                               md5" | sudo tee -a /etc/postgresql/*/main/pg_hba.conf
        sudo service postgresql restart
    fi
    
    # Create databases if they don't exist
    for DB in aurite_db aurite_test_db; do
        if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB; then
            echo "Creating database: $DB"
            sudo -u postgres createdb -O aurite_user $DB
        else
            echo "Database $DB already exists"
        fi
    done
    
    echo "Initializing database schema..."
    cd src && python3 -m aurite_txtai.scripts.init_db

db-init:
    cd src && python3 -m aurite_txtai.scripts.init_db

db-reset:
    #!/usr/bin/env bash
    echo "Resetting databases..."
    dropdb -U aurite_user aurite_db --if-exists
    dropdb -U aurite_user aurite_test_db --if-exists
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