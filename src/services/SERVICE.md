# Txtai Service Architecture

## Overview

The txtai service architecture consists of three core components:

- `embeddings_service.py` - Core document management and indexing
- `query_service.py` - Search operations (semantic, SQL, hybrid)
- `config_service.py` - Configuration management
- `llm_service.py` - LLM functionality through txtai

## Component Details

### 1. Embeddings Service (embeddings_service.py)

Handles document indexing and storage:

```python
class EmbeddingsService:
    def add(self, documents: List[Dict[str, Any]]) -> int:
        """Add documents with metadata stored in tags"""
        formatted_docs = [
            (doc["id"], doc["text"], json.dumps(doc["metadata"]))
            for doc in documents
        ]
        self.embeddings.index(formatted_docs)
```

Key responsibilities:

- Document indexing
- Metadata storage in tags
- Index management

### 2. Query Service (query_service.py)

Provides three search types:

1. **Semantic Search**:

```python
# Pure semantic similarity search
results = query_service.semantic_search("machine learning", limit=10)
```

2. **SQL Search**:

```python
# Direct SQL queries with metadata filtering
sql_query = '''
    SELECT id, text, tags
    FROM txtai
    WHERE tags LIKE '%"category": "tech"%'
'''
results = query_service.sql_search(sql_query)
```

3. **Hybrid Search**:

```python
# Combines semantic and term matching (configured in txtai_config.py)
results = query_service.hybrid_search("machine learning", limit=10)
```

### 3. LLM Service (llm_service.py)

Provides LLM functionality through txtai:

## Critical Implementation Details

### 1. Document Structure

Documents must include:

```python
{
    "id": "unique_id",
    "text": "Document content",
    "metadata": {
        "category": "tech",
        "tags": ["ML", "computing"],
        "priority": 1
    }
}
```

### 2. Metadata Handling

Metadata is stored in the 'tags' column:

```python
# Correct way to query metadata
sql_query = '''
    SELECT id, text, tags
    FROM txtai
    WHERE tags LIKE '%"category": "tech"%'
'''
```

### 3. Search Results

All search methods return consistent results:

```python
{
    "id": "doc1",
    "text": "Document content",
    "score": 0.75,  # Only for semantic and hybrid search
    "metadata": {
        "category": "tech",
        "tags": ["ML", "computing"],
        "priority": 1
    }
}
```

## Configuration

Hybrid search settings in txtai_config.py:

```python
base_config = {
    "hybrid": True,
    "scoring": {
        "method": "bm25",
        "terms": True,
        "normalize": True,
        "weights": {
            "hybrid": 0.7,  # Semantic weight
            "terms": 0.3    # Term matching weight
        }
    }
}
```

## Common Patterns

### 1. Adding Documents

```python
service = EmbeddingsService()
service.initialize()
service.add([
    {
        "id": "doc1",
        "text": "content",
        "metadata": {"category": "tech"}
    }
])
```

### 2. Searching Documents

```python
# Create query service
query_service = QueryService(embeddings_service.embeddings, settings)

# Semantic search
semantic_results = query_service.semantic_search("query")

# SQL search with metadata
sql_results = query_service.sql_search('''
    SELECT * FROM txtai
    WHERE tags LIKE '%"category": "tech"%'
''')

# Hybrid search
hybrid_results = query_service.hybrid_search("query")
```

## Testing

Run service tests:

```bash
# Test embeddings service
python -m src.services.embeddings_service

# Test query service
python -m src.services.query_service

# Run all tests
pytest src/tests/test_services/
```

## Common Pitfalls

1. **Metadata Storage**:

   - ✅ Store in 'tags' column
   - ❌ Don't use 'metadata' column

2. **SQL Queries**:

   - ✅ Use triple quotes for SQL
   - ✅ Use double quotes for JSON patterns
   - ❌ Don't escape quotes in patterns

3. **Search Configuration**:
   - ✅ Configure hybrid search in txtai_config.py
   - ❌ Don't set weights in search calls

## LLM SERVICE

Basic generation

```python
response = llm_service.generate("What is machine learning?")
```

Context-based generation

```python
response = llm_service.generate_with_context(
    question="What is ML?",
    context="Machine learning is..."
)
```

Key responsibilities:

```plaintext
- Text generation
- RAG-style context-based responses
- Message formatting
- Error handling
```

## LLM Configuration

LLM settings in settings.py:

```python
LLM_PROVIDER="anthropic" # or "openai"
ANTHROPIC_API_KEY="..."
OPENAI_API_KEY="..."
```
