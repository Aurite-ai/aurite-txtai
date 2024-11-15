from fastapi import APIRouter, Depends
from services.data_processing import DataProcessingService
from services.db.client import DatabaseClient
from middleware.security import verify_api_key

router = APIRouter(prefix="/trends", dependencies=[Depends(verify_api_key)])
db = DatabaseClient()
processor = DataProcessingService()

@router.get("/")
async def get_trends(limit: int = 10):
    return db.fetch_all(
        """
        SELECT t.*, c.category 
        FROM trends t
        JOIN content c ON t.content_id = c.id
        ORDER BY t.created_at DESC
        LIMIT %s
        """,
        (limit,)
    )

@router.get("/{category}")
async def get_category_trends(category: str):
    return db.fetch_all(
        """
        SELECT t.*, c.category 
        FROM trends t
        JOIN content c ON t.content_id = c.id
        WHERE c.category = %s
        ORDER BY t.created_at DESC
        """,
        (category,)
    )
