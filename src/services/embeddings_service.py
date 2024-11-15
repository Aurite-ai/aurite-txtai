from txtai.embeddings import Embeddings
from src.services.config_service import config_service

class EmbeddingsService:
    def __init__(self):
        # Configure embeddings with GCS backend and content storage
        config = config_service.embeddings_config
        config["content"] = True  # Enable content storage
        config["path"] = config_service.settings.EMBEDDINGS_MODEL
        self.embeddings = Embeddings(config)

    def add(self, documents: list):
        """Index a list of documents with their metadata into the embeddings database"""
        # Convert documents to format expected by txtai
        indexed_docs = []
        for i, doc in enumerate(documents):
            # Handle both dict and string inputs
            if isinstance(doc, dict):
                indexed_docs.append((i, doc["text"], doc.get("metadata")))
            else:
                indexed_docs.append((i, doc, None))
        
        # Index documents
        self.embeddings.index(indexed_docs)
        self.embeddings.save()
        return len(indexed_docs)

    def simple_search(self, query: str, limit: int = 5):
        """Perform a simple semantic search using txtai embeddings"""
        return self.embeddings.search(query, limit)

    def hybrid_search(self, query: str, limit: int = 5):
        """Perform a hybrid search combining semantic and keyword matching"""
        results = self.embeddings.search(
            f"""
            select text, score as semantic,
                   bm25(text, '{query}') as keyword,
                   metadata
            from txtai 
            where similar('{query}')
            order by (semantic + keyword) / 2 desc
            limit {limit}
            """
        )
        
        return [{
            "text": result["text"],
            "scores": {
                "semantic": result["semantic"],
                "keyword": result["keyword"]
            },
            "metadata": result.get("metadata")
        } for result in results]
