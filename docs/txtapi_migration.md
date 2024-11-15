# TxtAI API Migration Notes

## Key Components to Preserve

1. FastAPI Setup

- Health check endpoint
- API key verification middleware
- Basic error handling

2. Dependencies

- fastapi==0.112.1
- httpx==0.27.0 (for async HTTP client)
- pydantic==2.8.2
- sqlalchemy==2.0.32
- uvicorn==0.30.6

3. Project Structure

- Separation of routes and services
- Configuration management
- Database operations
