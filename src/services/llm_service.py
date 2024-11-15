from typing import List, Optional, Union
from txtai import LLM
from .config_service import config_service
import os
import logging

logger = logging.getLogger(__name__)

class LLMService:
    """Service for managing LLM operations"""
    
    def __init__(self):
        """Initialize LLM service with configuration"""
        self._llm = None
        self.initialize_llm()
    
    def initialize_llm(self):
        """Initialize the LLM configuration"""
        try:
            # Set API keys for the provider
            os.environ["OPENAI_API_KEY"] = config_service.settings.OPENAI_API_KEY
            os.environ["ANTHROPIC_API_KEY"] = config_service.settings.ANTHROPIC_API_KEY
            
            if config_service.settings.LLM_PROVIDER == "anthropic":
                # Use Claude with litellm provider
                self._llm = LLM("anthropic/claude-3-sonnet-20240229")
            else:
                # Use GPT-4 with litellm provider
                self._llm = LLM("openai/gpt-4-turbo-preview")
                
            logger.info(f"LLM initialized with provider: {config_service.settings.LLM_PROVIDER}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            raise
    
    def _format_messages(self, messages: Union[str, List[dict]]) -> List[dict]:
        """Format messages for the LLM API
        
        Args:
            messages: Input messages as string or list of message dicts
            
        Returns:
            Properly formatted message list
        """
        if isinstance(messages, str):
            return [{"role": "user", "content": messages}]
        return messages
    
    def generate(self, prompt: Union[str, List[dict]]) -> str:
        """Generate text response for a prompt
        
        Args:
            prompt: Input prompt text or message list
            
        Returns:
            Generated response text
        """
        try:
            messages = self._format_messages(prompt)
            return self._llm(messages)
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            return "I apologize, but I encountered an error processing your request."
    
    def generate_with_context(self, question: str, context: str) -> str:
        """Generate response using RAG-style prompt with context
        
        Args:
            question: Question to answer
            context: Context text to use for answering
            
        Returns:
            Generated response text
        """
        try:
            messages = [
                {
                    "role": "system", 
                    "content": """You are a helpful AI assistant. You must ONLY answer questions using the provided context.
                    If the answer cannot be found in the context, you must clearly state that the information is not 
                    available in the given context. Do not make assumptions or provide information from outside the context."""
                },
                {
                    "role": "user", 
                    "content": f"""Answer this question using ONLY the context below. If the answer is not in the context, 
                    say that you cannot answer based on the given context.

                    Context: {context}

                    Question: {question}

                    Answer:"""
                }
            ]
            return self._llm(messages)
        except Exception as e:
            logger.error(f"Context generation failed: {str(e)}")
            return "I apologize, but I encountered an error processing your request."

# Global LLM service instance
llm_service = LLMService() 