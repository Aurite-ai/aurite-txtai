from fastapi import APIRouter, HTTPException
from src.services import registry

router = APIRouter()


@router.post("/start")
async def start_stream_listener():
    """Start the stream listener"""
    try:
        await registry.stream_service.start_listening()
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_stream_listener():
    """Stop the stream listener"""
    try:
        await registry.stream_service.stop_listening()
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def stream_status():
    """Get stream service status"""
    try:
        return {
            "initialized": registry.stream_service.initialized,
            "listening": registry.stream_service._listening,
            "streams": registry.stream_service.streams,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
