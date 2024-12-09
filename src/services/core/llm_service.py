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
    provider: str


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
                    "provider": self.settings.LLM_PROVIDER,
                }
                logger.info(f"LLM Config: {self._config}")

                self._initialized = True
                logger.info(f"LLM initialized successfully with provider: {self.settings.LLM_PROVIDER}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e!s}")
            raise

    def _prepare_completion_params(
        self,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> dict[str, Any]:
        """Prepare completion parameters based on provider

        Args:
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            dict[str, Any]: Provider-specific completion parameters
        """
        if self._config is None:
            raise RuntimeError("LLM config not initialized")

        params = {
            "temperature": temperature,
        }

        # Handle max_tokens based on provider
        if self._config["provider"] == "anthropic":
            params["max_tokens_to_sample"] = max_tokens
        else:
            params["max_tokens"] = max_tokens

        return params

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

            # Validate prompt
            if not prompt or not prompt.strip():
                logger.warning("Empty prompt provided")
                return ""

            # Format messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Get provider-specific parameters
            completion_params = self._prepare_completion_params(temperature, max_tokens)

            # Generate response (completion is not async)
            response = completion(
                model=self._config["path"],
                messages=messages,
                api_key=self._config["api_key"],
                **completion_params,
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

            # Validate messages
            if not messages or not all(msg.get("content") and msg.get("role") for msg in messages):
                logger.warning("Invalid message format")
                return ""

            # Format messages with optional system prompt
            formatted_messages = []
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})
            formatted_messages.extend(messages)

            # Get provider-specific parameters
            completion_params = self._prepare_completion_params(temperature, max_tokens)

            # Generate response (completion is not async)
            response = completion(
                model=self._config["path"],
                messages=formatted_messages,
                api_key=self._config["api_key"],
                **completion_params,
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
