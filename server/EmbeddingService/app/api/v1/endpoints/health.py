from fastapi import APIRouter

from app.utils.logger import logger

router = APIRouter()


@router.get("/health")
def health_check():
    """
    Health check endpoint to verify if the service is running.
    """
    logger.info("Health check endpoint called.")
    return {"status": "ok", "message": "Service is running."}
