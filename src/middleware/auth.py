"""Authentication middleware for API endpoints"""

from __future__ import annotations

import logging
import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# API key header configuration
api_key_header = APIKeyHeader(name="Authorization", auto_error=True)


async def verify_token(api_key: Annotated[str, Security(api_key_header)]) -> bool:
    """Verify the API token from request header.

    Args:
        api_key: API key from request header in 'Bearer <token>' format

    Returns:
        bool: True if token is valid

    Raises:
        HTTPException: If token is invalid or missing
    """
    try:
        # Extract token from "Bearer <token>" format
        if not api_key.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization header format",
            )

        token = api_key.split(" ")[1]
        expected_token = os.getenv("API_KEY")

        if not expected_token:
            logger.error("API_KEY environment variable not set")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API key configuration error",
            )

        if token != expected_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key",
            )

        return True

    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authorization header format",
        )
    except Exception as e:
        logger.error(f"Token verification error: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )


async def get_api_key(api_key: Annotated[str, Security(api_key_header)]) -> str:
    """Get and validate API key from request header.

    Args:
        api_key: API key from request header in 'Bearer <token>' format

    Returns:
        str: Validated API key token

    Raises:
        HTTPException: If token is invalid or missing
    """
    try:
        # Extract token from "Bearer <token>" format
        if not api_key.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization header format",
            )

        token = api_key.split(" ")[1]
        expected_token = os.getenv("API_KEY")

        if not expected_token:
            logger.error("API_KEY environment variable not set")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API key configuration error",
            )

        if token != expected_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key",
            )

        return token

    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authorization header format",
        )
    except Exception as e:
        logger.error(f"Token validation error: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )
