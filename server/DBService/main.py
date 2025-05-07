import os
import logging
import asyncpg
import uvicorn
import httpx
import json
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
load_dotenv()

# Config from env
HF_API_URL = os.getenv("HF_API_URL", "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2")
HF_API_TOKEN = os.getenv("HF_API_TOKEN","")

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "your-default-password")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "postgres")

DB_DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# ---------------- Models ----------------

class Chunk(BaseModel):
    chunk_id: int
    text: str

class Document(BaseModel):
    uri: Optional[str] = None
    video_id: Optional[str] = None
    chunks: List[Chunk]

class StoreRequest(BaseModel):
    documents: List[Document]
    tag: str
    session_id: str

class SearchRequest(BaseModel):
    query: str
    tag: str
    session_id: str
    top_k: int = 5

# --------------- Embedding ----------------

async def get_embedding(text: str) -> List[float]:
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(HF_API_URL, headers=headers, json={"inputs": text})
        if response.status_code != 200:
            logger.error(f"HF API error: {response.text}")
            raise HTTPException(status_code=500, detail="Embedding API error")
        return response.json()

# --------------- Database Logic ----------------

async def store_chunk(conn, chunk: Chunk, tag: str, embedding: List[float], uri: Optional[str], video_id: Optional[str], session_id: str):
    embedding_str = json.dumps(embedding)
    await conn.execute("""
        INSERT INTO documents (content, chunk_id, tag, embedding, uri, video_id, session_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, chunk.text, chunk.chunk_id, tag, embedding_str, uri, video_id, session_id)

async def search_chunks(conn, embedding: List[float], tag: str, session_id: str, top_k: int):
    embedding_str = json.dumps(embedding)
    rows = await conn.fetch("""
        SELECT id, content, chunk_id, tag, uri, video_id, session_id
        FROM documents
        WHERE tag = $1 AND session_id = $2
        ORDER BY embedding <-> $3
        LIMIT $4
    """, tag, session_id, embedding_str, top_k)
    return [dict(row) for row in rows]

async def get_total_chunks(conn, tag: str, session_id: str):
    row = await conn.fetchrow("""
        SELECT 
            session_id AS session, 
            tag,
            COUNT(*) AS row_count
        FROM 
            documents
        WHERE
            session_id = $1 AND tag = $2
        GROUP BY 
            session_id, tag
    """, session_id, tag)
    if row:
        return row['row_count']
    else:
        return -1

# ---------------- Endpoints ----------------

@app.post("/store")
async def store_documents(request: StoreRequest):
    logger.info(f"Storing documents under session: {request.session_id}, tag: {request.tag}")
    try:
        conn = await asyncpg.connect(DB_DSN)
        for doc in request.documents:
            for chunk in doc.chunks:
                embedding = await get_embedding(chunk.text)
                await store_chunk(
                    conn,
                    chunk,
                    request.tag,
                    embedding,
                    doc.uri,
                    doc.video_id,
                    request.session_id
                )
        await conn.close()
        return {"message": "Chunks stored successfully."}
    except Exception as e:
        logger.exception("Storage error")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_documents(request: SearchRequest):
    logger.info(f"Searching for session: {request.session_id}, tag: {request.tag}")
    try:
        conn = await asyncpg.connect(DB_DSN)
        query_embedding = await get_embedding(request.query)
        results = await search_chunks(conn, query_embedding, request.tag, request.session_id, request.top_k)
        await conn.close()
        return {"results": results}
    except Exception as e:
        logger.exception("Search error")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/totalChunks")
async def get_total_chunks_endpoint(
    tag: str = Query(...),
    session_id: str = Query(...)
):
    logger.info(f"Total chunks requested for session: {session_id}, tag: {tag}")
    try:
        conn = await asyncpg.connect(DB_DSN)
        total_chunks = await get_total_chunks(conn, tag, session_id)
        await conn.close()
        total_chunks = 5 if total_chunks == -1 else total_chunks
        return {
            "status": "ok",
            "total": total_chunks
        }
    except Exception as e:
        logger.exception("Get total chunks error")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    logger.info("Health check requested")
    return {"status": "ok"}

@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {"message": "DB Service is running"}

# -------------- Run Server ----------------

if __name__ == "__main__":
    logger.info("Starting DB Service....")
    uvicorn.run("dv_service:app", port=8003, reload=True)
    logger.info("DB Service started successfully.")
