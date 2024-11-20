from typing import List, Optional, Union, Dict, Any
from litellm import completion
import logging
from ..base_service import BaseService
from src.config import Settings

logger = logging.getLogger(__name__)


def create_llm_config(settings: Settings) -> dict:
    """Create LLM configuration"""
    return {
        "path": settings.LLM_MODELS[settings.LLM_PROVIDER],
        "api_key": (
            settings.ANTHROPIC_API_KEY
            if settings.LLM_PROVIDER == "anthropic"
            else settings.OPENAI_API_KEY
        ),
    }


class LLMService(BaseService):
    """Service for managing LLM operations"""

    def __init__(self):
        """Initialize LLM service"""
        super().__init__()
        self.settings: Optional[Settings] = None
        self._config: Optional[Dict[str, Any]] = None

    async def initialize(self, settings: Settings = None):
        """Initialize LLM service"""
        if not self.initialized:
            try:
                # Get or create settings
                self.settings = settings or Settings()

                # Get LLM config
                self._config = create_llm_config(self.settings)
                logger.info(f"LLM Config: {self._config}")

                # Mark as initialized
                self._initialized = True
                logger.info(
                    f"LLM initialized successfully with provider: {self.settings.LLM_PROVIDER}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {str(e)}")
                raise

    async def generate(self, prompt: Union[str, List[Dict[str, str]]]) -> str:
        """Generate text from prompt"""
        self._check_initialized()

        try:
            logger.info(f"Generating response for prompt: {prompt}")

            # Format messages
            if isinstance(prompt, str):
                messages = [
                    {"role": "system", "content": self.settings.SYSTEM_PROMPTS["default"]},
                    {"role": "user", "content": prompt},
                ]
            else:
                messages = prompt

            logger.info(f"Formatted messages: {messages}")

            # Generate response - litellm.completion is synchronous
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
            return f"Error: {str(e)}"

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
                    "content": f"Answer this question using ONLY the context below:\n\nContext: {context}\n\nQuestion: {question}\n\nAnswer:",
                },
            ]

            logger.info(f"Formatted messages: {messages}")

            # Generate response - litellm.completion is synchronous
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
            return f"Error: {str(e)}"


# Global service instance
llm_service = LLMService()
