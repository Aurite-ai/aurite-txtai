"""Test document fixtures"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def get_test_documents() -> List[Dict[str, Any]]:
    """Get standard test documents"""
    docs = [
        {
            "id": "doc1",
            "text": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience.",
            "metadata": {
                "category": "tech",
                "tags": ["ML", "AI"],
                "priority": 1,
            },
        },
        {
            "id": "doc2",
            "text": "Natural language processing (NLP) is a branch of AI that helps computers understand human language.",
            "metadata": {
                "category": "tech",
                "tags": ["NLP", "AI"],
                "priority": 2,
            },
        },
        {
            "id": "doc3",
            "text": "Artificial intelligence and machine learning are transforming how we process and analyze data.",
            "metadata": {
                "category": "tech",
                "tags": ["AI", "ML", "Data"],
                "priority": 3,
            },
        },
    ]
    logger.info(f"\n=== Test Documents ===")
    logger.info(f"Created {len(docs)} test documents")
    for doc in docs:
        logger.info(f"Document: {doc}")
    return docs


def get_edge_case_documents() -> List[Dict[str, Any]]:
    """Get edge case test documents"""
    return [
        {
            "id": "edge1",
            "text": "",  # Empty text
            "metadata": {},
        },
        {
            "id": "edge2",
            "text": "Test document with minimal metadata",
            "metadata": None,  # Missing metadata
        },
    ]
