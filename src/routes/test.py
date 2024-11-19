from fastapi import APIRouter, HTTPException
from src.services.communication_service import communication_service

router = APIRouter()


@router.get("/test/redis")
async def test_redis():
    """Test Redis connection"""
    try:
        ping = await communication_service._redis_client.ping()
        return {"status": "connected" if ping else "error"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check with Redis status"""
    try:
        redis_status = "connected" if await communication_service._redis_client.ping() else "error"
        return {"status": "healthy", "redis": redis_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
