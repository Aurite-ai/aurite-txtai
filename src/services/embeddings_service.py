from txtai.embeddings import Embeddings
from src.services.config_service import config_service

class EmbeddingsService:
    def __init__(self):
        # Configure embeddings with GCS backend
        self.embeddings = Embeddings(config_service.embeddings_config)
        
        # Create bucket if it doesn't exist
        config_service.init_storage()

    def simple_search(self, query: str, limit: int = 5):
        """Perform a simple semantic search using txtai embeddings"""
        return self.embeddings.search(query, limit)

    def index_documents(self, documents: list):
        """Index a list of documents into the embeddings database"""
        self.embeddings.index(documents)
        self.embeddings.save()

    def hybrid_search(self, query: str, limit: int = 5):
        """Perform a hybrid search combining semantic and keyword matching"""
        results = self.embeddings.search(
            f"""
            select text, score as semantic,
                   bm25(text, '{query}') as keyword
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
            }
        } for result in results]
