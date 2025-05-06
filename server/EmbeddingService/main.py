from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import logging
import uvicorn

app = FastAPI()
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)
# ========== Logging Setup ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

class TextInput(BaseModel):
    inputs: str

@app.post("/embed")
def generate_embedding(data: TextInput):
    try:
        logger.info(f"Received input for embedding: {data.inputs}")
        # Generate embedding using the model
        embedding = model.encode(data.inputs).tolist()
        logger.info(f"Generated embedding")
        return embedding
    except Error as e:
        logger.error(f"Error: {e}")
        return {"error": str(e)}

# -------------- Run Server ----------------

if __name__ == "__main__":
    logger.info("Starting Embedding Service...")
    uvicorn.run("dv_service:app", port=8004, reload=True)
    logger.info("Embedding Service started successfully.")