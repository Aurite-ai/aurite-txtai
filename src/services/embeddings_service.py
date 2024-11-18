from pathlib import Path
import json
import logging
from typing import List, Dict, Any, Optional
from uuid import uuid4

from txtai.embeddings import Embeddings

from .config_service import config_service

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service to manage txtai embeddings lifecycle"""

    def __init__(self):
        self.settings = config_service.settings
        self.embeddings: Optional[Embeddings] = None
        self.initialize()

    def initialize(self):
        """Initialize embeddings with config"""
        try:
            config = config_service.embeddings_config
            logger.info("Initializing embeddings...")
            self.embeddings = Embeddings(config)
            # Initialize empty index
            self.embeddings.index([])
            logger.info("Embeddings initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {str(e)}")
            raise

    def add(self, documents: List[Dict[str, Any]]) -> int:
        """Add documents to embeddings index"""
        if not self.embeddings:
            raise ValueError("Embeddings not initialized")

        try:
            # Log initial documents
            logger.info("\n=== Document Processing ===")
            logger.info(f"Input documents: {json.dumps(documents, indent=2)}")

            # Format documents for txtai indexing
            formatted_docs = []
            for doc in documents:
                # Generate UUID if no id provided
                doc_id = str(doc.get("id", str(uuid4())))

                # Convert metadata to JSON string
                metadata = json.dumps(doc.get("metadata", {}))

                # Create tuple of (id, text, metadata)
                formatted_doc = (doc_id, doc["text"], metadata)
                formatted_docs.append(formatted_doc)

                # Log each document's transformation
                logger.info(f"\nDocument transformation:")
                logger.info(f"Original: {json.dumps(doc, indent=2)}")
                logger.info(f"Formatted: {formatted_doc}")
                logger.info(f"Metadata (raw): {metadata}")
                logger.info(f"Metadata (parsed): {json.loads(metadata)}")

            # Log before indexing
            logger.info("\n=== Pre-Indexing State ===")
            logger.info(f"Number of documents to index: {len(formatted_docs)}")
            logger.info(f"Formatted documents: {formatted_docs}")

            # Index the documents
            self.embeddings.index(formatted_docs)

            # Verify indexing with a SQL query
            logger.info("\n=== Post-Indexing Verification ===")
            verify_query = "SELECT id, text, metadata FROM txtai"
            results = self.embeddings.search(verify_query)
            logger.info(f"Indexed documents: {json.dumps(results, indent=2)}")

            return len(formatted_docs)

        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise

    def hybrid_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform hybrid search on indexed documents"""
        if not self.embeddings:
            raise ValueError("Embeddings not initialized")

        try:
            logger.info("\n=== Search Process ===")
            logger.info(f"Query: {query}")
            logger.info(f"Limit: {limit}")

            # Perform hybrid search
            logger.info("\nPerforming hybrid search:")
            results = self.embeddings.search(query, limit)
            logger.info(f"Raw search results: {json.dumps(results, indent=2)}")

            # Get full document data including tags (metadata)
            doc_ids = [result["id"] for result in results]
            id_list = ",".join([f"'{id}'" for id in doc_ids])  # Quote the IDs
            sql_query = f"""
                SELECT id, text, tags
                FROM txtai
                WHERE id IN ({id_list})
            """
            full_docs = self.embeddings.search(sql_query)  # Remove doc_ids parameter
            logger.info(f"Full docs: {json.dumps(full_docs, indent=2)}")

            # Create id to tags mapping
            id_to_tags = {doc["id"]: doc.get("tags") for doc in full_docs}

            # Format results
            formatted_results = []
            for result in results:
                logger.info(f"\nProcessing result: {json.dumps(result, indent=2)}")

                # Get metadata from tags
                metadata = {}
                tags_str = id_to_tags.get(result["id"])
                if tags_str:
                    try:
                        metadata = json.loads(tags_str)
                        logger.info(
                            f"Parsed metadata from tags: {json.dumps(metadata, indent=2)}"
                        )
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse tags as metadata: {str(e)}")
                        logger.warning(f"Raw tags: {tags_str}")
                else:
                    logger.warning("No tags found for document")

                # Format result
                formatted_result = {
                    "id": result["id"],
                    "text": result["text"],
                    "score": result["score"],
                    "metadata": metadata,
                }
                formatted_results.append(formatted_result)
                logger.info(
                    f"Formatted result: {json.dumps(formatted_result, indent=2)}"
                )

            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise


# Global service instance
embeddings_service = EmbeddingsService()

if __name__ == "__main__":
    import logging
    from pathlib import Path

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    # Test documents matching notebook pattern
    test_docs = [
        {
            "id": "doc1",
            "text": "Machine learning models require significant computational resources",
            "metadata": {
                "category": "tech",
                "tags": ["ML", "computing"],
                "priority": 1,
            },
        },
        {
            "id": "doc2",
            "text": "Natural language processing advances with transformer models",
            "metadata": {"category": "tech", "tags": ["NLP", "ML"], "priority": 2},
        },
    ]

    def inspect_embeddings():
        """Debug function to inspect embeddings state"""
        try:
            service = embeddings_service

            # Log config
            logger.info("\n=== Configuration ===")
            logger.info(
                f"Embeddings config: {json.dumps(config_service.embeddings_config, indent=2)}"
            )

            # Log initial state
            logger.info("\n=== Initial State ===")
            logger.info(f"Embeddings initialized: {service.embeddings is not None}")
            if service.embeddings:
                logger.info(
                    f"Embeddings config: {json.dumps(service.embeddings.config, indent=2)}"
                )

            # Add documents
            logger.info("\n=== Adding Documents ===")
            count = service.add(test_docs)
            logger.info(f"Added {count} documents")

            # Test different search types
            logger.info("\n=== Testing Search Types ===")

            # Direct SQL query
            logger.info("\nDirect SQL Query:")
            sql_results = service.embeddings.search("SELECT * FROM txtai")
            logger.info(f"SQL results: {json.dumps(sql_results, indent=2)}")

            # Metadata SQL query
            logger.info("\nMetadata SQL Query:")
            metadata_results = service.embeddings.search(
                'SELECT * FROM txtai WHERE metadata LIKE \'%"category":"tech"%\''
            )
            logger.info(f"Metadata results: {json.dumps(metadata_results, indent=2)}")

            # Hybrid search
            logger.info("\nHybrid Search:")
            hybrid_results = service.hybrid_search("machine learning", limit=2)
            logger.info(f"Hybrid results: {json.dumps(hybrid_results, indent=2)}")

        except Exception as e:
            logger.error(f"Inspection failed: {str(e)}", exc_info=True)

    # Run inspection
    logger.info("Starting embeddings service inspection...")
    inspect_embeddings()
