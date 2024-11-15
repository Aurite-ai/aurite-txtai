from typing import List, Optional, Dict, Any
from txtai.embeddings import Embeddings
from rank_bm25 import BM25Okapi
import numpy as np

class EmbeddingsService:
    def __init__(self):
        # Initialize embeddings with default configuration
        self.embeddings = Embeddings({
            "path": "sentence-transformers/nli-mpnet-base-v2"
        })
        self.documents: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None
        
    def add(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to both embeddings and BM25 indices."""
        # Store documents for reference
        start_id = len(self.documents)
        self.documents.extend(documents)
        
        # Prepare data for embeddings index
        data = [(i, doc["text"], None) for i, doc in enumerate(documents, start=start_id)]
        
        # Add to embeddings index
        self.embeddings.index(data)
        
        # Prepare and add to BM25 index
        tokenized_docs = [doc["text"].lower().split() for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_docs)
        
    def search(self, query: str, limit: int = 3, hybrid_weight: float = 0.5) -> List[Dict[str, Any]]:
        """Search using hybrid approach (semantic + keyword).
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            hybrid_weight: Weight for semantic search (0.0 to 1.0)
                         0.0 = BM25 only, 1.0 = Semantic only
        """
        if not self.documents:
            return []
            
        # Get semantic search scores
        semantic_results = self.embeddings.search(query, len(self.documents))
        semantic_scores = {uid: score for uid, score in semantic_results}
        
        # Get BM25 scores
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Normalize BM25 scores
        bm25_scores = bm25_scores / max(bm25_scores) if max(bm25_scores) > 0 else bm25_scores
        
        # Combine scores using weighted average
        combined_scores = []
        for idx in range(len(self.documents)):
            semantic_score = semantic_scores.get(idx, 0.0)
            bm25_score = bm25_scores[idx]
            
            # Weighted combination
            combined_score = (hybrid_weight * semantic_score + 
                            (1 - hybrid_weight) * bm25_score)
            
            combined_scores.append((idx, combined_score))
        
        # Sort by combined score and get top results
        results = sorted(combined_scores, key=lambda x: x[1], reverse=True)[:limit]
        
        # Return formatted results
        return [
            {
                "score": score,
                "document": self.documents[uid],
                "scores": {
                    "semantic": semantic_scores.get(uid, 0.0),
                    "keyword": bm25_scores[uid],
                    "combined": score
                }
            }
            for uid, score in results
        ]
