from txtai import Embeddings
from typing import List, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

class EmbeddingsService:
    def __init__(self):
        """Initialize the embeddings service with default configuration"""
        self.embeddings = self.create_index("default")

    @staticmethod
    def create_index(name: str) -> Embeddings:
        """Create a new embeddings index with specified configuration"""
        config = {
            "path": "sentence-transformers/nli-mpnet-base-v2",
            "content": True,
            "backend": "faiss",
            "hybrid": True,
            "scoring": {
                "method": "bm25",
                "terms": True,
                "normalize": True
            },
            "batch": 32,
            "normalize": True,
            "defaults": False
        }
        
        embeddings = Embeddings(config)
        return embeddings

    def add(self, documents: List[Dict[str, Any]]) -> int:
        """Add documents to the default index"""
        return self.add_documents(self.embeddings, documents)

    def count(self) -> int:
        """Get total document count in default index"""
        results = self.embeddings.search("select count(*) as total from txtai")
        return results[0]["total"] if results else 0

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the default index"""
        return self.semantic_search(self.embeddings, query, limit)

    @staticmethod
    def add_documents(index: Embeddings, documents: List[Dict[str, Any]]) -> int:
        """Add documents to index while preserving metadata"""
        indexed_docs = []
        for i, doc in enumerate(documents):
            indexed_docs.append({
                "id": str(i),
                "text": doc["text"],
                "metadata": doc.get("metadata", {})
            })
        
        index.index(indexed_docs)
        return len(documents)

    @staticmethod
    def semantic_search(index: Embeddings, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search with metadata preservation"""
        sql = f"""
        SELECT text, score, metadata 
        FROM txtai 
        WHERE similar('{query}')
        LIMIT {limit}
        """
        
        results = index.search(sql)
        
        for result in results:
            if isinstance(result.get("metadata"), str):
                try:
                    result["metadata"] = json.loads(result["metadata"])
                except (json.JSONDecodeError, TypeError):
                    result["metadata"] = {}
            elif "metadata" not in result:
                result["metadata"] = {}
                
        return results
