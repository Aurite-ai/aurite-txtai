from typing import List, Optional, Union
from txtai import LLM
import os
import logging
from .config_service import config_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LLMService:
    """Service for managing LLM operations"""

    def __init__(self):
        """Initialize LLM service"""
        logger.info("Initializing LLM service...")
        self._llm = None
        self.initialize_llm()

    def initialize_llm(self):
        """Initialize the LLM configuration"""
        try:
            # Get LLM config
            llm_config = config_service.llm_config
            logger.info(f"LLM Config: {llm_config}")

            # Initialize LLM
            self._llm = LLM(**llm_config)

            logger.info(
                f"LLM initialized successfully with provider: {config_service.settings.LLM_PROVIDER}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}", exc_info=True)
            raise

    def generate(self, prompt: Union[str, List[dict]]) -> str:
        """Generate text response"""
        try:
            logger.info(f"Generating response for prompt: {prompt}")
            messages = [
                {"role": "system", "content": config_service.settings.SYSTEM_PROMPTS["default"]},
                {
                    "role": "user",
                    "content": prompt if isinstance(prompt, str) else prompt[0]["content"],
                },
            ]
            logger.info(f"Formatted messages: {messages}")
            response = self._llm(messages)
            logger.info(f"Generated response: {response}")
            return response
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}", exc_info=True)
            return "I apologize, but I encountered an error processing your request."

    def generate_with_context(self, question: str, context: str) -> str:
        """Generate response with context"""
        try:
            logger.info(f"Generating response for question: {question}")
            logger.info(f"With context: {context}")
            messages = [
                {"role": "system", "content": config_service.settings.SYSTEM_PROMPTS["rag"]},
                {
                    "role": "user",
                    "content": f"""Answer this question using ONLY the context below:

Context: {context}

Question: {question}

Answer:""",
                },
            ]
            logger.info(f"Formatted messages: {messages}")
            response = self._llm(messages)
            logger.info(f"Generated response: {response}")
            return response
        except Exception as e:
            logger.error(f"Context generation failed: {str(e)}", exc_info=True)
            return "I apologize, but I encountered an error processing your request."


# Global service instance
logger.info("Creating LLM service instance...")
llm_service = LLMService()

if __name__ == "__main__":
    try:
        # Test the service
        logger.info("\nTesting basic generation...")
        response = llm_service.generate("What is machine learning?")
        logger.info(f"Basic response: {response}\n")

        logger.info("\nTesting generation with context...")
        context = "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience."
        response = llm_service.generate_with_context("What is machine learning?", context)
        logger.info(f"Context response: {response}\n")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
