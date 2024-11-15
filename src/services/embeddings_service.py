from typing import List, Optional, Dict, Any
from txtai.embeddings import Embeddings

class EmbeddingsService:
    def __init__(self):
        # Initialize embeddings with default configuration
        # Using sentence-transformers model as shown in notebook 01
        self.embeddings = Embeddings({
            "path": "sentence-transformers/nli-mpnet-base-v2"
        })
        self.documents: List[Dict[str, Any]] = []
        
    def add(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the embeddings index.
        
        Args:
            documents: List of documents with text and optional metadata
        """
        # Store documents for reference
        start_id = len(self.documents)
        self.documents.extend(documents)
        
        # Create list of (id, text, None) tuples
        data = [(i, doc["text"], None) for i, doc in enumerate(documents, start=start_id)]
        
        # Add to embeddings index
        self.embeddings.index(data)
        
    def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Search for documents similar to query.
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            
        Returns:
            List of documents with scores
        """
        # Run the similarity search
        results = self.embeddings.search(query, limit)
        
        # Map results to original documents
        return [
            {
                "score": score,
                "document": self.documents[uid]
            }
            for uid, score in results
        ]
