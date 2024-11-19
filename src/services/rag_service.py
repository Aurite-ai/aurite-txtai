from typing import List, Optional, Dict, Any
from txtai import RAG
import logging
import json
from .embeddings_service import embeddings_service
from .llm_service import llm_service
from .config_service import config_service
from .communication_service import communication_service
from ..models.messages import Message, MessageType

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
                system=config_service.settings.SYSTEM_PROMPTS["rag"],
            )
            logger.info("RAG service initialized successfully")

            # Subscribe to RAG requests
            self._start_listeners()

        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {str(e)}", exc_info=True)
            raise

    def _start_listeners(self):
        """Start listening for RAG requests"""
        try:
            # Listen for Node.js requests
            stream = config_service.settings.CHANNELS["rag"]
            while True:
                messages = communication_service.subscribe_to_node(stream)
                for msg in messages:
                    self._handle_rag_request(msg)

        except Exception as e:
            logger.error(f"Error in RAG listener: {str(e)}")

    def _handle_rag_request(self, message: Dict):
        """Handle incoming RAG request"""
        try:
            # Process RAG request
            result = self.generate(
                question=message["data"]["question"], limit=message["data"].get("limit", 3)
            )

            # Publish result back to Node.js
            communication_service.publish_to_node(
                config_service.settings.CHANNELS["rag"],
                {
                    "type": MessageType.RAG_REQUEST,
                    "data": result,
                    "session_id": message.get("session_id"),
                },
            )

        except Exception as e:
            logger.error(f"Error handling RAG request: {str(e)}")

    def search_context(self, query: str, limit: int = 3, min_score: float = 0.3) -> List[Dict]:
        """Search for relevant context using embeddings"""
        try:
            logger.info(f"\n=== Context Search ===")
            logger.info(f"Query: {query}")
            logger.info(f"Limit: {limit}")

            # Use embeddings service for search
            results = embeddings_service.hybrid_search(query, limit)

            # Filter by minimum score
            results = [r for r in results if r.get("score", 0) >= min_score]
            logger.info(f"Found {len(results)} relevant documents")

            return results
        except Exception as e:
            logger.error(f"Context search failed: {str(e)}", exc_info=True)
            raise

    def generate(self, question: str, limit: int = 3) -> Dict[str, Any]:
        """Generate response using RAG pipeline"""
        try:
            if not question or not question.strip():
                raise ValueError("Question cannot be empty")

            logger.info("\n=== RAG Generation ===")
            logger.info(f"Question: {question}")

            # First get relevant context
            context = self.search_context(question, limit)
            if not context:
                return {
                    "answer": "No relevant context found to answer this question.",
                    "context": [],
                    "citations": [],
                }

            # Format prompt for RAG pipeline
            prompt = {
                "query": question,
                "question": question,
                "context": " ".join([doc["text"] for doc in context]),
                "limit": limit,
            }

            # Generate response
            result = self.rag([prompt])[0]
            logger.info(f"Generated response: {json.dumps(result, indent=2)}")

            return {
                "answer": result["answer"],
                "context": context,
                "citations": [{"text": c["text"], "score": c.get("score", 0)} for c in context],
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
