import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.api_router import api_router
from .utils.logger import logger

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router
    #    , prefix="/api/v1"
)

# -------------- Run Server ----------------


def run_server():
    logger.info("Starting Embedding Service...")
    uvicorn.run("app.main:app", port=8004, reload=True)
    logger.info("Embedding Service started successfully.")


if __name__ == "__main__":
    run_server()
