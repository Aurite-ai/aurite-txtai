from txtai import Embeddings
from typing import List, Dict, Any, Optional
import logging
from .config_service import config_service

logger = logging.getLogger(__name__)

class EmbeddingsService:
    """Service for managing embeddings operations"""
    
    def __init__(self):
        """Initialize embeddings service with configuration"""
        self._embeddings = None
        self._custom_indices = {}
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
    
    def add(self, documents: List[Dict[str, Any]]) -> int:
        """Add documents to the embeddings index
        
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
    
    def create_custom_index(self, name: str, config: Optional[Dict] = None) -> None:
        """Create a custom embeddings index with optional configuration
        
        Args:
            name: Name of the custom index
            config: Optional configuration overrides
        """
        try:
            # Merge base config with custom overrides
            index_config = config_service.embeddings_config.copy()
            if config:
                index_config.update(config)
            
            # Create new embeddings instance
            self._custom_indices[name] = Embeddings(index_config)
            logger.info(f"Created custom index: {name}")
        except Exception as e:
            logger.error(f"Failed to create custom index {name}: {str(e)}")
            raise
    
    def add_to_custom_index(self, name: str, documents: List[Dict[str, Any]]) -> int:
        """Add documents to a custom index
        
        Args:
            name: Name of the custom index
            documents: List of documents to add
            
        Returns:
            Number of documents added
        """
        try:
            if name not in self._custom_indices:
                raise ValueError(f"Custom index {name} does not exist")
                
            self._custom_indices[name].index(documents)
            return len(documents)
        except Exception as e:
            logger.error(f"Failed to add to custom index {name}: {str(e)}")
            raise
    
    def search_custom_index(self, name: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search a custom index
        
        Args:
            name: Name of the custom index
            query: Search query text
            limit: Maximum number of results
            
        Returns:
            List of search results with scores
        """
        try:
            if name not in self._custom_indices:
                raise ValueError(f"Custom index {name} does not exist")
                
            sql = f"""
            SELECT text, score, metadata
            FROM txtai 
            WHERE similar('{query}')
            ORDER BY score DESC
            LIMIT {limit}
            """
            results = self._custom_indices[name].search(sql)
            return self._process_results(results)
        except Exception as e:
            logger.error(f"Failed to search custom index {name}: {str(e)}")
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
