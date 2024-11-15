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
            "indexes": {
                "sparse": {
                    "bm25": {
                        "terms": True,
                        "normalize": True
                    }
                },
                "dense": {}
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

    def semantic_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the default index"""
        return self._semantic_search(self.embeddings, query, limit)

    def hybrid_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword matching"""
        try:
            sql = f"""
            SELECT text, score, metadata
            FROM txtai 
            WHERE similar('{query}') OR bm25('{query}')
            ORDER BY score DESC
            LIMIT {limit}
            """
            logger.info(f"Executing hybrid search SQL: {sql}")
            results = self.embeddings.search(sql)
            logger.info(f"Raw search results: {results}")
            return self.process_results(results)
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            raise

    @staticmethod
    def add_documents(index: Embeddings, documents: List[Dict[str, Any]]) -> int:
        """Add documents to index while preserving metadata"""
        indexed_docs = []
        for i, doc in enumerate(documents):
            # Ensure metadata is a dict and JSON serializable
            metadata = doc.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
                
            indexed_docs.append({
                "id": str(i),
                "text": doc["text"],
                "metadata": json.dumps(metadata)  # Serialize metadata
            })
        
        index.index(indexed_docs)
        return len(documents)

    @staticmethod
    def _semantic_search(index: Embeddings, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Internal method for semantic search with metadata preservation"""
        # Use SQL query to ensure metadata is returned properly
        sql = f"""
        SELECT text, score, metadata
        FROM txtai 
        WHERE similar('{query}')
        LIMIT {limit}
        """
        results = index.search(sql)
        return EmbeddingsService.process_results(results)

    @staticmethod
    def process_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and normalize search results"""
        processed = []
        for result in results:
            # Create new result dict
            processed_result = {
                "text": result["text"],
                "score": float(result.get("score", 0.0)),  # Ensure score is float
                "metadata": {}
            }
            
            # Handle metadata
            metadata = result.get("metadata")
            if isinstance(metadata, str):
                try:
                    processed_result["metadata"] = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    pass
            elif isinstance(metadata, dict):
                processed_result["metadata"] = metadata
                
            processed.append(processed_result)
                
        return processed
