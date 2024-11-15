import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.services.llm_service import llm_service

@pytest.fixture
def test_context():
    return """
    txtai is an all-in-one embeddings database for semantic search, LLM orchestration and language model workflows.
    The main programming language with txtai is Python. A key tenet is that the underlying data in an embeddings index 
    is accessible without txtai.
    """

def test_llm_generate():
    """Test basic text generation"""
    response = llm_service.generate("Write a short greeting in 5 words")
    
    # Check that response is a non-empty string
    assert isinstance(response, str)
    assert len(response) > 0
    
    # Check word count is approximately 5 (allowing some flexibility)
    words = response.split()
    assert 3 <= len(words) <= 7

def test_llm_generate_with_context(test_context):
    """Test RAG-style generation with context"""
    question = "What is the main programming language used by txtai?"
    response = llm_service.generate_with_context(question, test_context)
    
    # Check that response is a non-empty string
    assert isinstance(response, str)
    assert len(response) > 0
    
    # Response should mention Python since it's in the context
    assert "Python" in response

def test_llm_out_of_context(test_context):
    """Test that model sticks to provided context"""
    question = "What is the capital of France?"
    response = llm_service.generate_with_context(question, test_context)
    
    # Response should indicate information is not in context
    assert any(phrase in response.lower() for phrase in [
        "context does not",
        "information is not",
        "cannot answer",
        "no information",
        "not mentioned",
        "not provided",
        "not contain",
        "does not include",
        "unable to find",
        "i apologize",
        "the context only",
        "the provided context",
        "based on the context",
        "in the given context",
        "from the context",
        "context provided",
        "context discusses",
        "context is about",
        "outside the scope"
    ])

def test_llm_initialization():
    """Test that LLM service initializes properly"""
    assert llm_service._llm is not None
    
    # Test basic functionality to ensure initialization worked
    response = llm_service.generate("Echo back the word 'test'")
    assert isinstance(response, str)
    assert len(response) > 0

def test_message_format():
    """Test direct message format input"""
    messages = [
        {"role": "system", "content": "You are a test assistant."},
        {"role": "user", "content": "Say 'hello'"}
    ]
    response = llm_service.generate(messages)
    assert isinstance(response, str)
    assert len(response) > 0 