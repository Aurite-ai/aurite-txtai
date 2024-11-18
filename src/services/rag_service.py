from typing import List, Optional, Dict, Any
from txtai import RAG
import logging
import json
from .embeddings_service import embeddings_service
from .llm_service import llm_service
from .config_service import config_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RAGService:
    """Service for Retrieval Augmented Generation operations"""

    def __init__(self):
        """Initialize RAG service with embeddings and LLM"""
        try:
            logger.info("Initializing RAG service...")

            # Ensure embeddings are initialized
            if not embeddings_service.embeddings:
                embeddings_service.initialize()
                logger.info("Initialized embeddings service")

            # Define template for RAG pipeline
            template = """Answer this question using ONLY the context below. If the answer cannot be found in the context, clearly state that.

Context: {context}

Question: {question}

Answer:"""

            # Initialize RAG pipeline with embeddings and LLM
            self.rag = RAG(
                similarity=embeddings_service.embeddings,
                path=config_service.settings.LLM_MODELS[config_service.settings.LLM_PROVIDER],
                api_key=(
                    config_service.settings.ANTHROPIC_API_KEY
                    if config_service.settings.LLM_PROVIDER == "anthropic"
                    else config_service.settings.OPENAI_API_KEY
                ),
                template=template,
            )
            logger.info("RAG service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {str(e)}", exc_info=True)
            raise

    def search_context(self, query: str, limit: int = 3) -> List[Dict]:
        """Search for relevant context using embeddings"""
        try:
            logger.info(f"\n=== Context Search ===")
            logger.info(f"Query: {query}")
            logger.info(f"Limit: {limit}")

            # Use embeddings service for search
            results = embeddings_service.hybrid_search(query, limit)
            logger.info(f"Found {len(results)} relevant documents")

            return results
        except Exception as e:
            logger.error(f"Context search failed: {str(e)}", exc_info=True)
            raise

    def generate(self, question: str, limit: int = 3) -> Dict[str, Any]:
        """Generate response using RAG pipeline"""
        try:
            logger.info("\n=== RAG Generation ===")
            logger.info(f"Question: {question}")

            # Format prompt for RAG pipeline
            prompt = {"query": question, "question": question, "limit": limit}

            # Generate response
            result = self.rag([prompt])[0]
            logger.info(f"Generated response: {json.dumps(result, indent=2)}")

            return {
                "answer": result["answer"],
                "context": result.get("context", []),
                "citations": [
                    {"text": c["text"], "score": c.get("score", 0)}
                    for c in result.get("context", [])
                ],
            }

        except Exception as e:
            logger.error(f"RAG generation failed: {str(e)}", exc_info=True)
            raise


# Global RAG service instance
logger.info("Creating RAG service instance...")
rag_service = RAGService()

if __name__ == "__main__":
    # Test the service
    try:
        # Add test documents
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
                "metadata": {
                    "category": "tech",
                    "tags": ["NLP", "ML"],
                    "priority": 2,
                },
            },
        ]
        embeddings_service.add(test_docs)
        logger.info("Added test documents")

        # Test context search
        logger.info("\nTesting context search...")
        results = rag_service.search_context("machine learning", 2)
        logger.info(f"Search results: {json.dumps(results, indent=2)}")

        # Test RAG generation
        logger.info("\nTesting RAG generation...")
        response = rag_service.generate("What is machine learning?")
        logger.info(f"RAG response: {json.dumps(response, indent=2)}")

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
