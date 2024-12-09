from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, TypedDict, cast

import httpx
from litellm import completion
from litellm.types.utils import ModelResponse

from src.services.base_service import BaseService


if TYPE_CHECKING:
    from src.config import Settings


logger = logging.getLogger(__name__)


class LLMConfig(TypedDict):
    """Type definition for LLM configuration"""

    path: str
    api_key: str


class LLMService(BaseService):
    """Service for managing LLM operations"""

    def __init__(self) -> None:
        """Initialize LLM service"""
        super().__init__()
        self._config: LLMConfig | None = None

    async def initialize(self, settings: Settings, **kwargs: Any) -> None:
        """Initialize LLM service with configuration

        Args:
            settings: Application settings
            **kwargs: Additional configuration options

        Raises:
            Exception: If initialization fails
        """
        try:
            await super().initialize(settings, **kwargs)

            if not self._initialized:
                # Set LLM config
                self._config = {
                    "path": self.settings.LLM_MODELS[self.settings.LLM_PROVIDER],
                    "api_key": (
                        self.settings.ANTHROPIC_API_KEY
                        if self.settings.LLM_PROVIDER == "anthropic"
                        else self.settings.LLM_API_KEY
                    ),
                }
                logger.info(f"LLM Config: {self._config}")

                self._initialized = True
                logger.info(f"LLM initialized successfully with provider: {self.settings.LLM_PROVIDER}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e!s}")
            raise

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate text using the configured LLM

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            str: Generated text response
        """
        try:
            self._check_initialized()
            if self._config is None:
                raise RuntimeError("LLM config not initialized")

            # Format messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Generate response
            response = await completion(
                model=self._config["path"],
                messages=messages,
                api_key=self._config["api_key"],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extract response text safely
            if not isinstance(response, ModelResponse):
                raise TypeError("Unexpected response type from LLM")

            if not response.choices or not response.choices[0].message:
                raise ValueError("No response content from LLM")

            response_text = cast(str, response.choices[0].message.content)
            if not response_text:
                raise ValueError("Empty response from LLM")

            logger.info(f"Generated response: {response_text}")
            return response_text

        except (ValueError, RuntimeError, httpx.HTTPError) as e:
            logger.error(f"Generation failed: {e!s}")
            return ""

    async def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Chat with the LLM using a message history

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            str: Generated response text
        """
        try:
            self._check_initialized()
            if self._config is None:
                raise RuntimeError("LLM config not initialized")

            # Format messages with optional system prompt
            formatted_messages = []
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})
            formatted_messages.extend(messages)

            # Generate response
            response = await completion(
                model=self._config["path"],
                messages=formatted_messages,
                api_key=self._config["api_key"],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extract response text safely
            if not isinstance(response, ModelResponse):
                raise TypeError("Unexpected response type from LLM")

            if not response.choices or not response.choices[0].message:
                raise ValueError("No response content from LLM")

            response_text = cast(str, response.choices[0].message.content)
            if not response_text:
                raise ValueError("Empty response from LLM")

            logger.info(f"Generated response: {response_text}")
            return response_text

        except (ValueError, RuntimeError, httpx.HTTPError) as e:
            logger.error(f"Chat failed: {e!s}")
            return ""


# Global service instance
llm_service = LLMService()
