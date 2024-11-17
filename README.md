# txtai Service with GCS Storage

A FastAPI service that provides semantic search and document embeddings using txtai with Google Cloud Storage integration.

## Overview

This service implements a production-ready wrapper around txtai's core functionality, providing:

- Document indexing with metadata support
- Semantic search
- Hybrid search (semantic + keyword)
- SQL-based querying
- Cloud storage persistence
- REST API endpoints

## Core Components

### Embeddings Service (`src/services/embeddings_service.py`)

The core service layer that wraps txtai functionality:

- Document management (add, delete)
- Search operations (semantic, hybrid, SQL)
- Index persistence (save/load)
- Cloud storage integration
- Metadata handling
- Error handling and logging

### API Routes (`src/routes/embeddings.py`)

REST endpoints exposing the embeddings functionality:

- `POST /api/embeddings/add` - Add documents with metadata
- `POST /api/embeddings/search` - Hybrid semantic + keyword search
- `POST /api/embeddings/semantic-search` - Pure semantic search
- `POST /api/embeddings/advanced-search` - Search with metadata filtering

### Main Application (`src/main.py`)

FastAPI application setup with:

- API documentation
- Health check endpoint
- Route registration
- Logging configuration

## Testing

The service includes comprehensive tests:

### API Tests (`test/test_api.py`)

Tests the REST endpoints:

- Document addition
- Search operations
- Response formats
- Error handling

### Embeddings Tests (`test/test_embeddings.py`)

Tests the core embeddings functionality:

- GCS connectivity
- Document operations
- Search accuracy
- Metadata handling
- Index persistence

## Features

1. **Document Management**

   - Batch document addition
   - Metadata support
   - Document deletion

2. **Search Capabilities**

   - Pure semantic search
   - Hybrid search with configurable weights
   - SQL-based querying
   - Metadata filtering

3. **Cloud Integration**

   - Google Cloud Storage support
   - Automatic index persistence
   - Cloud configuration management

4. **Production Features**
   - Error handling
   - Logging
   - Input validation
   - API documentation
   - Health monitoring

## Development

Built using:

- Python 3.12
- FastAPI
- txtai 6.0+
- Google Cloud Storage
- pytest for testing
