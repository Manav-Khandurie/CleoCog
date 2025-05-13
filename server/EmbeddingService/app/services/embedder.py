from binascii import Error
from sentence_transformers import SentenceTransformer
from app.utils.logger import logger
from app.utils.config import settings
from app.schemas.embed import TextInput

model = SentenceTransformer(settings.MODEL_NAME)

def generate_embedding(payload: TextInput):
    try:
        logger.info(f"Received input for embedding: {payload}")
        embedding = model.encode(payload).tolist()
        logger.info(f"Generated embedding {embedding[:50]}...")  # Log only the first 50 elements for brevity
        return embedding
    except Error as e:
        logger.error(f"Error: {e}")
        return {"error": str(e)}