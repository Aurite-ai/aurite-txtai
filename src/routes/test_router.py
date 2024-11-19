from fastapi import APIRouter
from src.services import registry

router = APIRouter()


@router.get("/redis")
async def test_redis():
    """Test Redis connection"""
    try:
        ping = await registry.communication_service.redis_client.ping()
        return {"status": "connected" if ping else "error"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/services")
async def service_status():
    """Get status of all services"""
    return {
        "config": registry.config_service.initialized,
        "embeddings": registry.embeddings_service.initialized,
        "llm": registry.llm_service.initialized,
        "rag": registry.rag_service.initialized,
        "communication": registry.communication_service.initialized,
        "stream": registry.stream_service.initialized,
    }
