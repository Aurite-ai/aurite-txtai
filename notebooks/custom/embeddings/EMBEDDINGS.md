# Embeddings Service Documentation

## Overview

The embeddings service provides vector search capabilities using txtai. It supports:

- Multiple storage backends (SQLite, Memory)
- Rich metadata handling
- Persistent index storage (including Google Cloud Storage)
- Hybrid search (combining semantic and keyword search)
- CRUD operations on documents

## Directory Structure

```tree
txtai/
└── test/
├── content.db # SQLite content storage
├── sqlite/ # SQLite index files
│ ├── config
│ ├── documents
│ └── embeddings
└── memory/ # Memory index files
├── config
├── documents
└── embeddings
```

## Configuration

Basic configuration example:

```python
config = {
    "path": "sentence-transformers/nli-mpnet-base-v2", # Model choice
    "content": True, # Enable content storage
    "contentpath": "txtai/test/content.db", # SQLite storage path
    "backend": "faiss", # Vector storage backend
    "hybrid": True, # Enable hybrid search
    "normalize": True # Normalize vectors
}
```

### Standard Document Format

The embeddings service expects documents to be in a specific format. This format is used to index and search documents.

```python
documents = [
    {
        "id": "doc1",
        "text": "Document content",
        "metadata": {
            "category": "tech",
            "tags": ["ML", "computing"],
            "priority": 1
        }
    }
]

# Convert for indexing
indexed_docs = [(doc["id"], doc["text"], json.dumps(doc["metadata"]))
                for doc in documents]
```

## Storage Types

1. **Memory Storage**:

   - Fast access
   - Non-persistent
   - Ideal for development

2. **SQLite Storage**:

   - Persistent storage
   - Better for production
   - Supports complex queries

3. **Cloud Storage**:
   - Remote persistence
   - Scalable storage
   - Cross-environment accessibility

### Storage Configuration Examples

#### SQLite Configuration

```python
sqlite_config = {
    "path": "sentence-transformers/nli-mpnet-base-v2",
    "content": True,
    "contentpath": "txtai/test/content.db",  # SQLite storage
    "backend": "faiss",
    "hybrid": True,
    "normalize": True
}
sqlite_embeddings = Embeddings(sqlite_config)
```

#### Memory Configuration

```python
memory_config = {
    "path": "sentence-transformers/nli-mpnet-base-v2",
    "content": True,  # In-memory storage
    "backend": "faiss",
    "hybrid": True,
    "normalize": True
}
memory_embeddings = Embeddings(memory_config)
```

#### Google Cloud Storage Configuration

```python
cloud_config = {
    "path": "sentence-transformers/nli-mpnet-base-v2",
    "content": True,
    "backend": "faiss",
    "hybrid": True,
    "scoring": {
        "method": "bm25",
        "terms": True,
        "normalize": True
    },
    "normalize": True,
    "cloud": {
        "provider": "gcs",
        "container": "your-bucket-name",
        "prefix": "txtai"
    }
}
cloud_embeddings = Embeddings(cloud_config)
```

#### Cloud Storage Operations

```python
# Save to cloud
cloud_path = "txtai/indices/my_index"
cloud_embeddings.save(cloud_path)

# Load from cloud
cloud_embeddings = Embeddings(cloud_config)
cloud_embeddings.load(cloud_path)
```

# Usage Examples (any configuration)

See `04_Embeddings_Usage.ipynb` to run the examples.

## Standard Operations

### Initialize Embeddings

```python
from txtai.embeddings import Embeddings

embeddings = Embeddings(config)
```

### Index Documents

```python
documents = [
    (0, "Document text", {"metadata": "value"}), # (id, text, metadata)
    (1, "Another document", {"tags": ["example"]})
]

embeddings.index(documents)
```

### Save/Load Index (Create/Load Operations)

```python
embeddings.save("txtai/test/my_index")
```

```python
new_embeddings = Embeddings(config)

new_embeddings.load("txtai/test/my_index")
```

### Search (Retrieve Operations)

```python
results = embeddings.search("search query", limit=2)

for result in results:
    print(f"Text: {result['text']}")
    print(f"Score: {result['score']}")
    print(f"Metadata: {result['metadata']}")
```

## Document Operations

### Add Documents (Index Operation)

```python
# Single document
doc = {
    "id": "doc1",
    "text": "Data visualization helps understand complex patterns",
    "metadata": {
        "category": "tech",
        "tags": ["visualization", "data"],
        "priority": 1
    }
}

# Convert and index
embeddings.index([(doc["id"], doc["text"], json.dumps(doc["metadata"]))])
```

```python
# Multiple documents
docs = [
    {
        "id": "doc1",
        "text": "First document content",
        "metadata": {"category": "tech"}
    },
    {
        "id": "doc2",
        "text": "Second document content",
        "metadata": {"category": "science"}
    }
]
embeddings.index([(doc["id"], doc["text"], json.dumps(doc["metadata"])) for doc in docs])
```

### Update Documents (Re-index Operation)

```python
# Update by re-indexing with same ID
doc_id = "doc1"
updated_text = "Updated document content"
updated_metadata = {
    "category": "tech",
    "tags": ["updated", "content"],
    "priority": 1
}

embeddings.index([(doc_id, updated_text, json.dumps(updated_metadata))])

# Verify update
results = embeddings.search("updated content", 1)
print(f"Updated text: {results[0]['text']}")
print(f"Score: {results[0]['score']}")
```

### Delete Documents

```python
# Delete single document
embeddings.delete(["doc1"])

# Delete multiple documents
embeddings.delete(["doc1", "doc2", "doc3"])

# Verify deletion
results = embeddings.search("deleted document content", 1)
if results[0]['score'] < 0.5:
    print("Document successfully deleted")
```

### Best Practices for Document Operations

1. **Document Format**:

   - Use consistent ID schemes
   - Always JSON encode metadata
   - Include relevant search metadata

2. **Operation Verification**:

   - Verify additions with search operations
   - Check update success with content comparison
   - Confirm deletions with score thresholds

3. **Batch Operations**:
   - Group related operations for efficiency
   - Use list comprehensions for conversions
   - Maintain consistent metadata structure

## Advanced Search Operations

### Basic Semantic Search

```python
results = embeddings.search("computational resources for AI", 1)
```

### Hybrid Search (Semantic + BM25)

```python
results = embeddings.search("machine learning infrastructure", 1)
```

### Save/Load Index

```python
embeddings.save("txtai/test/my_index")
```

```python
new_embeddings = Embeddings(config)

new_embeddings.load("txtai/test/my_index")
```

## Additional Best Practices

1. **Document Processing**:

   - Always JSON encode metadata
   - Use consistent ID schemes
   - Include relevant search metadata

2. **Search Optimization**:

   - Use hybrid search for better recall
   - Implement proper metadata filtering
   - Consider query complexity vs performance

3. **Cloud Operations**:
   - Implement proper error handling
   - Use environment variables for configuration
   - Monitor cloud storage usage

## Reference Notebooks

- `01_Embeddings_Overview.ipynb`: Basic concepts and usage
- `02_Content_Storage.ipynb`: Storage backend comparison
- `03_Cloud_Storage.ipynb`: Cloud integration patterns
- `04_Embeddings_Usage.ipynb`: Advanced search operations
