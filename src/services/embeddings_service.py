from txtai.embeddings import Embeddings
from fastapi import HTTPException
from src.services.config_service import config_service
import json
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class EmbeddingsService:
    """
    Service for managing txtai embeddings operations with cloud storage support.
    Based on txtai's recommended patterns for building embeddings indices.

    References:
        - Notebooks/01_Introducing_txtai.ipynb: Core concepts and features
        - Notebooks/64_Embeddings_index_format_for_open_data_access.ipynb: Index storage and access
    """
    
    def __init__(self):
        """
        Initialize embeddings with configuration and cloud storage.

        References:
            Notebooks/46_Whats_new_in_txtai_6_0.ipynb:
            ```python
            # Create embeddings with content storage enabled
            embeddings = Embeddings({
                "path": "sentence-transformers/nli-mpnet-base-v2",
                "content": True,  # Enable content storage for metadata
                "contentpath": "txtai-sqlite"  # Optional: specify SQLite storage path
            })
            ```
        """
        try:
            # Ensure content storage is enabled for metadata
            config = config_service.embeddings_config
            if not config.get("content"):
                config["content"] = True
                logger.info("Enabled content storage for metadata support")
            
            self.embeddings = Embeddings(config)
            logger.info("Embeddings service initialized with config: %s", 
                       {k: v for k, v in config.items() if k != 'cloud'})
        except Exception as e:
            logger.error("Failed to initialize embeddings: %s", str(e), exc_info=True)
            raise

    def _format_result(self, result: Dict[str, Any], include_hybrid_scores: bool = False, weight: float = None) -> Dict[str, Any]:
        """Format a single search result with optional hybrid scoring"""
        formatted = {
            "text": result.get("text", ""),
            "score": result.get("score", 0.0),
            "metadata": result.get("data", {}).get("metadata", {}) if result.get("data") else {}
        }
        
        if include_hybrid_scores and weight is not None:
            formatted["scores"] = {
                "semantic": result["score"] * weight,
                "keyword": result["score"] * (1.0 - weight)
            }
            
        return formatted

    def _format_results(self, results: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Format a list of search results"""
        return [self._format_result(r, **kwargs) for r in results]

    def _execute_search(self, query: str, limit: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Execute search with error handling and cloud storage support"""
        try:
            return self.embeddings.search(query, limit)
        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    def _prepare_document(self, doc: Union[Dict[str, Any], str, BaseModel], doc_id: int) -> Tuple[int, Dict[str, Any], None]:
        """
        Prepare a single document for upsert following txtai's recommended format:
        (id, data, None) where data contains text and optional metadata
        """
        # Handle Pydantic models
        if isinstance(doc, BaseModel):
            doc = doc.model_dump()
            
        return (
            doc_id,
            {
                "text": doc["text"] if isinstance(doc, dict) else doc,
                "metadata": doc.get("metadata") if isinstance(doc, dict) else None
            },
            None
        )

    def add(self, documents: Union[List[Dict[str, Any]], List[str], List[BaseModel]], batch_size: int = 100) -> int:
        """
        Add documents to the embeddings index using batched upsert for better performance.
        Documents are automatically saved to configured cloud storage.

        References:
            Notebooks/01_Introducing_txtai.ipynb:            ```python
            # Create an index for the list of text
            embeddings.index(data)            ```
        """
        try:
            # Convert documents to list if it's a Pydantic model
            if hasattr(documents, "documents"):
                documents = documents.documents
                
            total_docs = len(documents)
            for i in range(0, total_docs, batch_size):
                batch = documents[i:i + batch_size]
                upsert_docs = [
                    self._prepare_document(doc, idx + i)
                    for idx, doc in enumerate(batch)
                ]
                self.embeddings.upsert(upsert_docs)
                logger.info(f"Added batch of {len(batch)} documents ({i + len(batch)}/{total_docs})")
            
            # Save index to cloud storage if configured
            if config_service.embeddings_config.get("cloud"):
                cloud_config = config_service.embeddings_config["cloud"]
                path = f"{cloud_config['prefix']}/index"
                self.embeddings.save(path)
                logger.info(f"Saved index to cloud storage: {path}")
            
            return total_docs
            
        except Exception as e:
            logger.error("Failed to add documents: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    def delete(self, ids: List[int]) -> int:
        """
        Delete documents and update cloud storage.

        References:
            Notebooks/01_Introducing_txtai.ipynb:            ```python
            # Remove record from index
            embeddings.delete([0])            ```
        """
        try:
            self.embeddings.delete(ids)
            # Save index after successful deletion
            self.embeddings.save()
            logger.info(f"Successfully deleted {len(ids)} documents")
            return len(ids)
        except Exception as e:
            logger.error("Failed to delete documents: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    def simple_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform pure semantic search.

        References:
            Notebooks/01_Introducing_txtai.ipynb:            ```python
            # Run an embeddings search
            uid = embeddings.search(query, 1)[0][0]            ```
        """
        results = self._execute_search(query, limit)
        return self._format_results(results)

    def hybrid_search(self, query: str, limit: int = 5, weight: float = 0.7) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and keyword matching.
        weight parameter controls semantic (weight) vs keyword (1-weight) balance.

        References:
            Notebooks/01_Introducing_txtai.ipynb:            ```python
            # Create embeddings with subindexes
            embeddings = Embeddings(
              content=True,
              defaults=False,
              indexes={
                "keyword": {
                  "keyword": True
                },
                "dense": {
                  "path": "sentence-transformers/nli-mpnet-base-v2"
                }
              }
            )            ```
        """
        results = self._execute_search(query, limit, weights=(weight, 1.0 - weight))
        return self._format_results(results, include_hybrid_scores=True, weight=weight)

    def count(self) -> int:
        """
        Get total number of documents in the index.

        References:
            Notebooks/37_Embeddings_index_components.ipynb:        ```python
            # Get total number of records using SQL count
            embeddings.search("select count(*) from txtai")[0]["count(*)"]        ```
        """
        try:
            result = self.embeddings.search("select count(*) from txtai")
            return result[0]["count(*)"] if result else 0
        except Exception as e:
            logger.error("Failed to get document count: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    def sql_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute direct SQL queries against the embeddings database.
        
        References:
            Notebooks/01_Introducing_txtai.ipynb:        ```python
            # Run aggregate queries
            embeddings.search("select count(*), min(length), max(length), sum(length) from txtai")        ```
        """
        try:
            return self.embeddings.search(query)
        except Exception as e:
            logger.error(f"SQL search failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    def save(self, path: str) -> None:
        """
        Save embeddings index to specified path.
        
        References:
            Notebooks/01_Introducing_txtai.ipynb:        ```python
            embeddings.save("index")        ```
        """
        try:
            self.embeddings.save(path)
        except Exception as e:
            logger.error(f"Failed to save index: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    def load(self, path: str) -> None:
        """
        Load embeddings index from specified path.
        
        References:
            Notebooks/01_Introducing_txtai.ipynb:        ```python
            embeddings = Embeddings()
            embeddings.load("index")        ```
        """
        try:
            self.embeddings.load(path)
        except Exception as e:
            logger.error(f"Failed to load index: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
