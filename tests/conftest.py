import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aurite_txtai.services.db.models import Base

@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine"""
    DATABASE_URL = "postgresql+psycopg://aurite_user:autumnBank36@localhost:5432/aurite_test_db"
    engine = create_engine(DATABASE_URL)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a new database session for a test"""
    TestingSessionLocal = sessionmaker(bind=db_engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close() 