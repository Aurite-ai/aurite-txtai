from txtai import Embeddings
from typing import List, Dict, Any, Optional
import logging
from .config_service import config_service

logger = logging.getLogger(__name__)

class EmbeddingsService:
    """Service for managing embeddings operations"""
    
    # Class variables for storing indices and configs
    _indices = {}
    _configs = {}
    
    def __init__(self):
        """Initialize embeddings service with configuration"""
        self._embeddings = None
        self.initialize_embeddings()
    
    def initialize_embeddings(self):
        """Initialize the embeddings configuration"""
        try:
            # Create embeddings instance with config from config service
            self._embeddings = Embeddings(config_service.embeddings_config)
            logger.info("Embeddings service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {str(e)}")
            raise
    
    @classmethod
    def create_index(cls, name: str, config: Optional[Dict] = None) -> Embeddings:
        """Create a new embeddings index
        
        Args:
            name: Name of the index
            config: Optional configuration overrides
            
        Returns:
            Embeddings instance for the index
        """
        try:
            # Start with base config
            index_config = {
                "path": config_service.settings.EMBEDDINGS_MODEL,
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
                "normalize": True
            }
            
            # Update with any custom config
            if config:
                index_config.update(config)
            
            # Create new embeddings instance with config
            embeddings = Embeddings(index_config)
            
            # Store index and config
            cls._indices[name] = embeddings
            cls._configs[name] = index_config
            
            logger.info(f"Created custom index: {name}")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to create index {name}: {str(e)}")
            raise
    
    @classmethod
    def get_index(cls, name: str) -> Optional[Embeddings]:
        """Get an existing embeddings index
        
        Args:
            name: Name of the index
            
        Returns:
            Embeddings instance or None if not found
        """
        return cls._indices.get(name)
    
    @classmethod
    def list_indices(cls) -> List[str]:
        """List all available indices
        
        Returns:
            List of index names
        """
        return list(cls._indices.keys())
    
    @classmethod
    def delete_index(cls, name: str) -> bool:
        """Delete an embeddings index
        
        Args:
            name: Name of the index
            
        Returns:
            True if deleted, False if not found
        """
        try:
            if name in cls._indices:
                del cls._indices[name]
                del cls._configs[name]
                logger.info(f"Deleted index: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete index {name}: {str(e)}")
            raise
    
    @classmethod
    def add_documents(cls, index: Embeddings, documents: List[Dict[str, Any]]) -> int:
        """Add documents to a specific index
        
        Args:
            index: Embeddings instance to add to
            documents: List of documents to add
            
        Returns:
            Number of documents added
        """
        try:
            # Format documents for indexing
            data = [(doc["text"], doc.get("metadata", {})) for doc in documents]
            
            # Index documents
            index.index(data)
            logger.info(f"Added {len(documents)} documents to index")
            return len(documents)
        except Exception as e:
            logger.error(f"Failed to add documents to index: {str(e)}")
            raise
    
    def add(self, documents: List[Dict[str, Any]]) -> int:
        """Add documents to the default embeddings index
        
        Args:
            documents: List of documents with text and metadata
            
        Returns:
            Number of documents added
        """
        try:
            self._embeddings.index(documents)
            return len(documents)
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise
    
    def count(self) -> int:
        """Get total document count in index
        
        Returns:
            Total number of documents
        """
        try:
            results = self._embeddings.search("select count(*) as total from txtai")
            return results[0]["total"] if results else 0
        except Exception as e:
            logger.error(f"Failed to get count: {str(e)}")
            raise
    
    def semantic_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search on the embeddings index
        
        Args:
            query: Search query text
            limit: Maximum number of results
            
        Returns:
            List of search results with scores
        """
        try:
            sql = f"""
            SELECT text, score, metadata
            FROM txtai 
            WHERE similar('{query}')
            ORDER BY score DESC
            LIMIT {limit}
            """
            results = self._embeddings.search(sql)
            return self._process_results(results)
        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            raise
    
    def hybrid_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword matching
        
        Args:
            query: Search query text
            limit: Maximum number of results
            
        Returns:
            List of search results with scores
        """
        try:
            sql = f"""
            SELECT text, score, metadata
            FROM txtai 
            WHERE similar('{query}') OR bm25('{query}')
            ORDER BY score DESC
            LIMIT {limit}
            """
            results = self._embeddings.search(sql)
            return self._process_results(results)
        except Exception as e:
            logger.error(f"Hybrid search failed: {str(e)}")
            raise
    
    def _process_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process search results to ensure consistent format
        
        Args:
            results: Raw search results from txtai
            
        Returns:
            Processed results with consistent format
        """
        processed = []
        for result in results:
            # Ensure metadata is a dict
            metadata = result.get("metadata", {})
            if isinstance(metadata, str):
                try:
                    metadata = eval(metadata)  # Convert string repr of dict to dict
                except:
                    metadata = {}
            
            processed.append({
                "text": result.get("text", ""),
                "score": float(result.get("score", 0.0)),
                "metadata": metadata
            })
        return processed

# Global embeddings service instance
embeddings_service = EmbeddingsService()