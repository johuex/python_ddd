import uvicorn
from fastapi import FastAPI

from src.allocation.entrypoints.routes.main import api_router


fastapi_app = FastAPI()
fastapi_app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000, log_level="debug")
