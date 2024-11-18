# from typing import List, Optional, Dict, Any
# from txtai import RAG
# import logging
# import json
# from .embeddings_service import embeddings_service
# from .llm_service import llm_service
# from .config_service import config_service

# logger = logging.getLogger(__name__)


# class RAGService:
#     """Service for Retrieval Augmented Generation operations"""

#     def __init__(self):
#         """Initialize RAG service with embeddings and LLM"""
#         try:
#             # Ensure embeddings are initialized
#             if not embeddings_service.embeddings:
#                 embeddings_service.initialize()
#                 logger.info("Initialized embeddings service")

#             # Define template for RAG pipeline
#             template = """<|im_start|>system
# You are a helpful AI assistant. You must ONLY answer questions using the provided context.
# If the answer cannot be found in the context, you must clearly state that the information is not available in the given context.
# <|im_end|>
# <|im_start|>user
# Context: {context}

# Question: {question}

# Please provide a clear and concise answer based only on the context above.
# <|im_end|>
# <|im_start|>assistant"""

#             # Initialize RAG pipeline with embeddings and LLM
#             self.rag = RAG(
#                 embeddings=embeddings_service.embeddings,
#                 llm=llm_service._llm,
#                 template=template,
#                 output="reference",  # Enable citation tracking
#             )
#             logger.info("RAG service initialized successfully")

#         except Exception as e:
#             logger.error(f"Failed to initialize RAG service: {str(e)}")
#             raise

#     def generate(self, question: str, limit: int = 3) -> Dict[str, Any]:
#         """Generate response using RAG pipeline"""
#         try:
#             logger.info("\n=== RAG Generation ===")
#             logger.info(f"Question: {question}")

#             # Create prompt for RAG pipeline
#             prompt = [
#                 {
#                     "text": question,  # For embeddings search
#                     "query": question,  # For template substitution
#                 }
#             ]

#             # Generate response with citations
#             result = self.rag(prompt)[0]
#             logger.info(f"Generated response: {json.dumps(result, indent=2)}")

#             return {"answer": result["answer"], "citation": result.get("reference")}

#         except Exception as e:
#             logger.error(f"RAG generation failed: {str(e)}")
#             raise


# # Global RAG service instance
# rag_service = RAGService()

# if __name__ == "__main__":
#     # Setup logging
#     logging.basicConfig(level=logging.INFO)
#     logger = logging.getLogger(__name__)

#     def run_test_queries():
#         """Run test queries to demonstrate RAG functionality"""
#         try:
#             # Add test documents first
#             test_docs = [
#                 {
#                     "id": "doc1",
#                     "text": "Machine learning models require significant computational resources",
#                     "metadata": {
#                         "category": "tech",
#                         "tags": ["ML", "computing"],
#                         "priority": 1,
#                     },
#                 },
#                 {
#                     "id": "doc2",
#                     "text": "Natural language processing advances with transformer models",
#                     "metadata": {
#                         "category": "tech",
#                         "tags": ["NLP", "ML"],
#                         "priority": 2,
#                     },
#                 },
#             ]
#             embeddings_service.add(test_docs)
#             logger.info("Added test documents")

#             # Test single question
#             question = "What is machine learning?"
#             response = rag_service.generate(question)
#             logger.info(f"Question: {question}")
#             logger.info(f"Response: {json.dumps(response, indent=2)}")

#         except Exception as e:
#             logger.error(f"Test failed: {str(e)}", exc_info=True)

#     run_test_queries()
