import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException

from app.db_client import DBClient
from app.middleware.security import verify_api_key
from app.routes import trends

# Load environment variables from .env file
load_dotenv()

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "TrendAI"}


@app.get("/health")
def health_check():
    try:
        with DBClient() as db:
            result = db.fetch_one("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Database connection failed: {str(e)}"
        )


@app.get("/secure/data", dependencies=[Depends(verify_api_key)])
def get_secure_data():
    return {"data": "This is secured data"}


# Include the trends router
app.include_router(trends.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
