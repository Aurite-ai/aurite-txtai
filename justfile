# Default recipe to display help
default:
    @just --list

# Install dependencies
setup:
    pip install -r requirements.txt
    npm install -g newman

# Start the development server
dev:
    python -m src.main

# Run Postman collection tests with Newman
postman:
    newman run txtai-service.postman_collection.json

# Run both server and tests (in separate terminals)
test-api: dev postman

# Clean up pycache files
clean:
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete 