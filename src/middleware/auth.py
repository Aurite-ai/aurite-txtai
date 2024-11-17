from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from ..services.config_service import config_service

api_key_header = APIKeyHeader(name="Authorization", auto_error=True)

async def verify_token(api_key: str = Security(api_key_header)):
    """Verify the API token from request header

    Args:
        api_key: API key from request header

    Returns:
        True if valid

    Raises:
        HTTPException if invalid
    """
    try:
        # Extract token from "Bearer <token>" format
        if not api_key.startswith("Bearer "):
            raise HTTPException(status_code=403, detail="Invalid authorization header format")

        token = api_key.split(" ")[1]
        if token != config_service.settings.API_KEY:
            raise HTTPException(status_code=403, detail="Invalid API key")

        return True
    except IndexError:
        raise HTTPException(status_code=403, detail="Invalid authorization header format")

async def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """Get and validate API key from request header

    Args:
        api_key: API key from request header

    Returns:
        Validated API key

    Raises:
        HTTPException if invalid
    """
    try:
        # Extract token from "Bearer <token>" format
        if not api_key.startswith("Bearer "):
            raise HTTPException(status_code=403, detail="Invalid authorization header format")

        token = api_key.split(" ")[1]
        if token != config_service.settings.API_KEY:
            raise HTTPException(status_code=403, detail="Invalid API key")

        return token
    except IndexError:
        raise HTTPException(status_code=403, detail="Invalid authorization header format")