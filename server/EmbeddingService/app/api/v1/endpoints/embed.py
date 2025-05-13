from fastapi import APIRouter

from app.schemas.embed import TextInput
from app.services.embedder import generate_embedding
from app.utils.logger import logger

router = APIRouter()


@router.post("/embed")
def embed_text(data: TextInput):
    try:
        logger.info(f"Received input for embedding: {data.inputs}")
        embedding = generate_embedding(data.inputs)
        logger.info("Generated embedding successfully.")
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return {"error": str(e)}
