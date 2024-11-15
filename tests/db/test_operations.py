import pytest
from services.db.operations import DatabaseOperations
from services.db.models import Content, SocialPost

@pytest.mark.asyncio
async def test_store_content(db_client):
    db_ops = DatabaseOperations(db_client)
    
    # Test data
    test_data = {
        "category": "Technology",
        "platform": "Reddit",
        "post_id": "123",
        "author": "testuser",
        "url": "https://reddit.com/r/test/123"
    }
    
    # Store content
    content_id = await db_ops.store_content(test_data)
    assert content_id > 0
    
    # Verify content storage
    stored_content = db_client.query(Content).filter(Content.id == content_id).first()
    assert stored_content.category == test_data["category"]
    
    # Store and verify social post
    social_post_id = await db_ops.store_social_post(content_id, test_data)
    stored_post = db_client.query(SocialPost).filter(SocialPost.id == social_post_id).first()
    assert stored_post.platform == test_data["platform"]
    assert stored_post.author == test_data["author"] 