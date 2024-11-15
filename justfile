# Default recipe to display help
default:
    @just --list

# Install dependencies
pip-install:
    pip install -r requirements.txt

# Start the development server
dev:
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run Postman collection tests with Newman
postman:
    newman run txtai-service.postman_collection.json

# Run both server and tests (in separate terminals)
test-api: dev postman

# Clean up pycache files
clean:
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete 