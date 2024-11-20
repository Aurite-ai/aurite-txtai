from typing import Dict, Any
from litellm import completion
import logging
from ..base_service import BaseService
from src.config import Settings

logger = logging.getLogger(__name__)


class LLMService(BaseService):
    """Service for managing LLM operations"""

    def __init__(self):
        """Initialize LLM service"""
        super().__init__()
        self.settings = None
        self._config = None

    async def initialize(self, settings: Settings) -> None:
        """Initialize LLM service"""
        if not self.initialized:
            try:
                self.settings = settings

                # Set LLM config
                self._config = {
                    "path": self.settings.LLM_MODELS[self.settings.LLM_PROVIDER],
                    "api_key": (
                        self.settings.ANTHROPIC_API_KEY
                        if self.settings.LLM_PROVIDER == "anthropic"
                        else self.settings.OPENAI_API_KEY
                    ),
                }
                logger.info(f"LLM Config: {self._config}")

                self._initialized = True
                logger.info(
                    f"LLM initialized successfully with provider: {self.settings.LLM_PROVIDER}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {str(e)}")
                raise

    async def generate(self, prompt: str, system: str = None) -> str:
        """Generate text from prompt"""
        self._check_initialized()
        try:
            logger.info(f"Generating response for prompt: {prompt}")

            # Format messages with optional system prompt
            messages = [
                {"role": "system", "content": system or self.settings.SYSTEM_PROMPTS["default"]},
                {"role": "user", "content": prompt},
            ]

            logger.info(f"Formatted messages: {messages}")

            # Generate response
            response = completion(
                model=self._config["path"],
                messages=messages,
                api_key=self._config["api_key"],
            )
            response_text = response.choices[0].message.content
            logger.info(f"Generated response: {response_text}")
            return response_text

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    async def generate_with_context(self, question: str, context: str) -> str:
        """Generate text with context"""
        self._check_initialized()
        try:
            logger.info(f"Generating response for question: {question}")
            logger.info(f"With context: {context}")

            # Format messages with context
            messages = [
                {"role": "system", "content": self.settings.SYSTEM_PROMPTS["rag"]},
                {
                    "role": "user",
                    "content": (
                        f"Answer this question using ONLY the context below:\n\n"
                        f"Context: {context}\n\n"
                        f"Question: {question}\n\n"
                        f"Answer:"
                    ),
                },
            ]

            logger.info(f"Formatted messages: {messages}")

            # Generate response
            response = completion(
                model=self._config["path"],
                messages=messages,
                api_key=self._config["api_key"],
            )
            response_text = response.choices[0].message.content
            logger.info(f"Generated response: {response_text}")
            return response_text

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise


# Global service instance
llm_service = LLMService()
