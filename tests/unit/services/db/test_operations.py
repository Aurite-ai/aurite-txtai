import pytest

from src.services.db.models import Content, Domain, Platform, SocialPost
from src.services.db.operations import DatabaseOperations


@pytest.mark.asyncio
class TestDatabaseOperations:
    async def test_store_content(self, db_session):
        db_ops = DatabaseOperations(db_session)

        test_data = {
            "domain": Domain.TECHNOLOGY,
            "platform": Platform.REDDIT,
            "post_id": "123",
            "author": "testuser",
            "url": "https://reddit.com/r/test/123",
        }

        # Test storing content
        content_id = await db_ops.store_content(test_data)
        assert content_id > 0

        # Verify storage
        stored_content = db_session.query(Content).filter(Content.id == content_id).first()
        assert stored_content.domain == test_data["domain"]

        # Test storing social post
        social_post_id = await db_ops.store_social_post(content_id, test_data)
        stored_post = db_session.query(SocialPost).filter(SocialPost.id == social_post_id).first()
        assert stored_post.platform == test_data["platform"]
        assert stored_post.author == test_data["author"]

    async def test_get_trends(self, db_session):
        db_ops = DatabaseOperations(db_session)

        # First store some test data
        test_content = {"domain": Domain.TECHNOLOGY, "platform": Platform.REDDIT}
        content_id = await db_ops.store_content(test_content)

        # Get trends
        trends = await db_ops.get_trends(limit=10)
        assert isinstance(trends, list)
        if trends:
            assert "domain" in trends[0]
            assert "created_at" in trends[0]
