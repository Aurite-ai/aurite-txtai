from fastapi.security import APIKeyHeader
from fastapi import Security, HTTPException, status
import hashlib

from pydantic_settings import BaseSettings

from src.services.config_service import config_service

API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

def hash_key(key: str) -> str:
    """Create SHA-256 hash of API key"""
    return hashlib.sha256(key.encode()).hexdigest()

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if not api_key_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )
    api_key = api_key_header.split(" ")[1]
    
    # Hash the provided key and compare with stored hash
    if hash_key(api_key) != config_service.settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key

class Settings(BaseSettings):
    API_KEY: str
    
    class Config:
        env_file = ".env"