txtai Service Documentation body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; max-width: 1000px; margin: 0 auto; padding: 20px; color: #333; } pre { background-color: #f6f8fa; padding: 16px; border-radius: 6px; overflow-x: auto; } code { font-family: SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace; font-size: 85%; } h1, h2, h3 { border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; } .note { background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 10px 0; }

# txtai Service

A FastAPI service implementing hybrid search capabilities using txtai embeddings and BM25 keyword search.

## Features

- Semantic search using txtai embeddings
- Keyword search using BM25 algorithm
- Hybrid search combining both approaches with configurable weights
- Document metadata support
- RESTful API endpoints

## Prerequisites

- Python 3.8+
- just (command runner)
- Newman (for API testing)

## Installation

    git clone [repository-url]
    cd [repository-name]
    just pip-install

## Available Commands

    just --list          # Show available commands
    just pip-install     # Install dependencies
    just dev            # Start development server
    just postman        # Run Postman collection tests
    just test-api       # Run server and tests
    just clean          # Clean Python cache files

## API Endpoints

### Health Check

    GET /
    Response: {"status": "healthy"}

### Add Documents

    POST /api/embeddings/add
    Content-Type: application/json

    {
        "documents": [
            {
                "text": "Document text content",
                "metadata": {
                    "category": "example",
                    "type": "document"
                }
            }
        ]
    }

### Search Documents

    POST /api/embeddings/search
    Content-Type: application/json

    {
        "query": "search query text",
        "limit": 3,
        "hybrid_weight": 0.7
    }

**Note:** The hybrid_weight parameter controls the balance between semantic and keyword search:

- 1.0: Pure semantic search
- 0.0: Pure keyword search
- 0.5: Equal combination (default)

## Response Format

Search results include combined scores and individual scores for both semantic and keyword matching:

    {
        "results": [
            {
                "score": 0.6869,
                "document": {
                    "text": "Document content",
                    "metadata": { ... }
                },
                "scores": {
                    "semantic": 0.5527,
                    "keyword": 1.0000,
                    "combined": 0.6869
                }
            }
        ]
    }

## Testing

The service includes a Postman collection for API testing. The collection tests various search scenarios:

- Health check verification
- Document addition
- Italian cuisine search
- Soup dishes search
- Easy recipes search
- Hybrid weight search

## Development

The service is built with:

- FastAPI - Web framework
- txtai - Embeddings and semantic search
- rank-bm25 - Keyword search implementation
- Pydantic - Data validation

## Project Structure

    .
    ├── src/
    │   ├── main.py              # FastAPI application
    │   ├── routers/
    │   │   └── embeddings.py    # API endpoints
    │   └── services/
    │       └── embeddings_service.py  # Search implementation
    ├── test/
    │   └── embeddings.test.py   # Unit tests
    ├── requirements.txt         # Dependencies
    ├── justfile                # Command runner
    └── txtai-service.postman_collection.json  # API tests
