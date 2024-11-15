import asyncio
from aurite_txtai.services.db.models import Base
from aurite_txtai.services.db.client import DatabaseClient

async def init_db():
    client = DatabaseClient()
    
    # Create tables
    Base.metadata.create_all(bind=client.engine)
    
    print("Database initialized successfully")

if __name__ == "__main__":
    asyncio.run(init_db()) 