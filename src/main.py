from fastapi import FastAPI
from .routers import embeddings

app = FastAPI(title="txtai Service")

# Add routers
app.include_router(embeddings.router)

@app.get("/")
async def root():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)