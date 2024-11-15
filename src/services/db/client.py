from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseClient:
    def __init__(self, test_mode=False):
        db_name = "aurite_test_db" if test_mode else "aurite_db"
        self.DATABASE_URL = f"postgresql+psycopg://{os.getenv('DB_USER', 'aurite_user')}:{os.getenv('DB_PASSWORD', 'autumnBank36')}@{os.getenv('DB_HOST', 'localhost')}:5432/{db_name}"
        self.engine = create_engine(self.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()
        
    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close() 