# Default recipe (lists available commands)
default:
    @just --list

# Install dependencies
install:
    pip install -e .

# Run tests
test:
    pytest -v

# Start API server
serve:
    python scripts/start_api.py

# Run API server in development mode
dev:
    # Kill any existing process on port 8000
    -lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Check GCP authentication
check-auth:
    python scripts/check_gcp_auth.py

# Initialize test data
init-data:
    python scripts/init_search.py

# Run embeddings tests
test-embeddings:
    python scripts/test_embeddings.py

# Clean up Python cache files
clean:
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    find . -type d -name "*.egg-info" -exec rm -r {} +
    find . -type d -name "*.egg" -exec rm -r {} +
    find . -type d -name ".pytest_cache" -exec rm -r {} +
    find . -type d -name ".coverage" -exec rm -r {} +
    find . -type f -name ".coverage" -delete

# Reset environment
reset: clean
    rm -rf .venv
    python3 -m venv .venv
    . .venv/bin/activate && pip install -r requirements.txt