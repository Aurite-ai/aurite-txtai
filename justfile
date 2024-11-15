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

    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        source .venv/bin/activate
        pip install --upgrade pip
        pip install pip-tools build hatchling
    else
        source .venv/bin/activate
    fi

    # Install dependencies
    pip-compile requirements.in
    pip install -e .
    pip install -r requirements.txt

    # Install pre-commit hooks if not already installed
    if [ ! -f ".git/hooks/pre-commit" ]; then
        pre-commit install
    fi

    # Set up database if not already configured
    just db-setup

    echo "Setup complete! Run 'source .venv/bin/activate' to activate the environment"

# Database commands
db-setup:
    bash scripts/init_db.sh

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
