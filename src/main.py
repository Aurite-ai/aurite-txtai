from fastapi import FastAPI
from src.routes import embeddings

app = FastAPI(title="Search API")

app.include_router(embeddings.router)

@app.get("/")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)