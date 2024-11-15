from typing import Dict, Any
from sqlalchemy.orm import Session
from . import models

class DatabaseOperations:
    def __init__(self, db: Session):
        self.db = db
    
    async def store_content(self, data: Dict[str, Any]) -> int:
        """Store content and return content_id"""
        db_content = models.Content(
            domain=data['domain']
        )
        self.db.add(db_content)
        await self.db.commit()
        await self.db.refresh(db_content)
        return db_content.id
    
    async def store_social_post(self, content_id: int, data: Dict[str, Any]) -> int:
        """Store social media post data"""
        db_post = models.SocialPost(
            content_id=content_id,
            platform=data['platform'],
            post_id=data['post_id'],
            author=data['author'],
            url=data.get('url')
        )
        self.db.add(db_post)
        await self.db.commit()
        await self.db.refresh(db_post)
        return db_post.id

    async def get_trends(self, limit: int = 10):
        """Get recent trends"""
        query = self.db.query(models.Content)\
            .order_by(models.Content.created_at.desc())\
            .limit(limit)
        results = await query.all()
        return [{"domain": r.domain, "created_at": r.created_at} for r in results]