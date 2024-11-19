from typing import List, Optional, Union
from txtai import LLM
import logging
from .base_service import BaseService
from .config_service import config_service

logger = logging.getLogger(__name__)


class LLMService(BaseService):
    """Service for managing LLM operations"""

    def __init__(self):
        super().__init__()
        self._llm = None

    async def initialize(self):
        """Initialize LLM service"""
        if not self.initialized:
            try:
                # Get LLM config
                llm_config = config_service.llm_config
                logger.info(f"LLM Config: {llm_config}")

                # Initialize LLM
                self._llm = LLM(**llm_config)
                self._initialized = True

                logger.info(
                    f"LLM initialized successfully with provider: {config_service.settings.LLM_PROVIDER}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {str(e)}")
                raise

    def generate(self, prompt: Union[str, List[dict]]) -> str:
        """Generate text response"""
        self._check_initialized()
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
            logger.error(f"Generation failed: {str(e)}")
            return "I apologize, but I encountered an error processing your request."

    def generate_with_context(self, question: str, context: str) -> str:
        """Generate response with context"""
        self._check_initialized()
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
            logger.error(f"Context generation failed: {str(e)}")
            return "I apologize, but I encountered an error processing your request."


# Global service instance
llm_service = LLMService()
