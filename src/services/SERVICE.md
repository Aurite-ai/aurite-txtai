# Txtai Service Architecture

## Overview

The txtai service architecture consists of three core components that work together to provide semantic search capabilities:

- `config_service.py` - Central configuration management
- `embeddings_service.py` - Core embeddings functionality
- `query_service.py` - Search and query operations

## Component Details

### 1. Configuration Service (config_service.py)

The ConfigService manages all configuration and initialization:

```python
class ConfigService:
    def __init__(self):
        self.settings = Settings()
        self._api_config = None
        self.initialize_api()

    @property
    def embeddings_config(self) -> dict:
        return {
            "path": self.settings.EMBEDDINGS_MODEL,
            "content": True,
            "backend": "faiss",
            "hybrid": True,
            ...
        }
```

Key responsibilities:

- Environment variable management
- txtai configuration creation
- API initialization

### 2. Embeddings Service (embeddings_service.py)

Handles document management and indexing:

```python
class EmbeddingsService:
    def add(self, documents: List[Dict[str, Any]]) -> int:
        formatted_docs = [
            (doc["id"], doc["text"], json.dumps(doc["metadata"]))
            for doc in documents
        ]
        self.embeddings.index(formatted_docs)
```

Key responsibilities:

- Document indexing
- Metadata handling
- Index management

### 3. Query Service (query_service.py)

Manages search operations:

```python
class QueryService:
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        results = self.embeddings.search(query, limit)
        return self._process_results(results)
```

Key responsibilities:

- Search execution
- Result formatting
- Query optimization

## Critical Implementation Details

### 1. Document Structure

Documents must be formatted as tuples for indexing:

```python
(id, text, metadata_json) = (
    "doc1",
    "Document text",
    json.dumps({"category": "tech", "tags": ["ML"]})
)
```

### 2. Metadata Handling

**Important**: Metadata is stored in the 'tags' column of txtai's SQLite database:

```python
# Correct way to retrieve metadata
sql_query = """
    SELECT id, text, tags
    FROM txtai
    WHERE id IN (...)
"""
```

### 3. Search Operations

Three types of searches are supported:

1. **Semantic Search**:

```python
results = embeddings.search("query text", limit=10)
```

2. **SQL Search**:

```python
results = embeddings.search("SELECT * FROM txtai WHERE tags LIKE '%tech%'")
```

3. **Hybrid Search**:

```python
# Combines semantic similarity with SQL filtering
results = embeddings.search(
    "query text",
    limit=10,
    weights={"hybrid": 0.7, "terms": 0.3}
)
```

## Common Pitfalls

1. **Metadata Storage**:

   - ✅ Store in 'tags' column
   - ❌ Don't use 'metadata' column

2. **SQL Queries**:

   - ✅ Use string formatting for IDs
   - ❌ Don't use parameterized queries with `?`

3. **Document Formatting**:
   - ✅ Always JSON encode metadata
   - ❌ Don't pass raw dictionaries

## Testing and Verification

Test the service using:

```bash
python -m src.services.embeddings_service
```

This runs a comprehensive test suite that verifies:

- Document indexing
- Metadata persistence
- Search functionality
- Result formatting

## Debugging Tips

1. Use SQL queries to inspect the database:

```python
results = embeddings.search("SELECT * FROM txtai")
```

2. Check metadata storage:

```python
results = embeddings.search("SELECT id, text, tags FROM txtai")
```

3. Verify search results:

```python
logger.info(f"Raw results: {json.dumps(results, indent=2)}")
```
