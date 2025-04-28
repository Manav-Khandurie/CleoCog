import os
import logging
import requests
import uvicorn
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List
from typing import Optional
import boto3
# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
s3_client = boto3.client('s3')

# Environment Variables (with defaults)
DB_SERVICE_URL = os.getenv("DB_SERVICE_URL", "http://localhost:8003")
LLM_PROMPT_SERVICE_URL = os.getenv("LLM_PROMPT_SERVICE_URL", "http://localhost:8002")
EXTRACTOR_SERVICE_URL = os.getenv("EXTRACTOR_SERVICE_URL", "http://localhost:8001")

# FastAPI app
app = FastAPI()

class StoreRequest(BaseModel):
    session_id: str
    tag: str
    yt_list: Optional[List[str]] = None

# ----------------- Helper Functions -----------------

# Get S3 URIs for a given session_id
def get_s3_uris(session_id: str) -> list:
    bucket_name = os.getenv('S3_BUCKET_NAME')
    logger.info(f"Fetching S3 URIs for session_id: {session_id} from bucket: {bucket_name}")    
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=f"{session_id}/")

    uris = []
    for obj in response.get('Contents', []):
        key = obj['Key']
        if not key.endswith('/'):  # skip folder itself
            uris.append(f"s3://{bucket_name}/{key}")
    return uris

# ----------------- API Endpoints -----------------
@app.get("/")
async def root():
    return {"message": "Welcome to the Backend Service"}

@app.get("/databaseQuery")
async def query(request: Request):
    query_text = request.query_params.get("query")
    if not query_text:
        raise HTTPException(status_code=400, detail="Query parameter 'query' is required.")
    payload = {
        "query": query_text,
        "tag": request.query_params.get("tag", ""),  # Optional
        "session_id": request.query_params.get("session_id", ""),  # Optional
        "top_k": int(request.query_params.get("top_k", 5))
    }

    try:
        logger.info(f"Forwarding query to DBService: {payload}")
        response = requests.post(f"{DB_SERVICE_URL}/search", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error in /query: {e}")
        raise HTTPException(status_code=500, detail="Failed to query DBService.")

@app.get("/query")
async def combined_query(request: Request):
    query_text = request.query_params.get("query")
    if not query_text:
        raise HTTPException(status_code=400, detail="Query parameter 'query' is required.")

    db_payload = {
        "query": query_text,
        "tag": request.query_params.get("tag", ""),  # Optional
        "session_id": request.query_params.get("session_id", ""),  # Optional
        "top_k": int(request.query_params.get("top_k", 5))
    }

    try:
        # Step 1: Call Database Service
        logger.info(f"Calling Database Service with: {db_payload}")
        db_response = requests.post(f"{DB_SERVICE_URL}/search", json=db_payload)
        db_response.raise_for_status()
        db_data = db_response.json()
        logger.info(f"DB Service response: {db_data}")

        # Step 2: Extract relevant content
        logger.info("Extracting content from DB response")
        extracted_texts = []
        prompt_text = []
        logger.info("-------------------------------------------------")
        logger.info("-------------------------------------------------")
        logger.info("-------------------------------------------------")
        logger.info(f"DB response: {db_data}")
        for result in db_data.get('results', []):
            content = result.get('content', '').strip()
            if content:  # Make sure there's actual content
                extracted_texts.append(content)

        # Combine the content into a structured prompt
        context_text = "\n\n".join(extracted_texts)

        # Here we add the user's query and any instructions for the LLM to generate the best response
        combined_prompt = f"""
        The user has asked: "{query_text}"

        Here is some relevant information retrieved from the database:

        {context_text}

        Please answer the user's query based on the information above. Be concise and clear.
        """

        logger.info(f"Combined prompt text prepared with {len(extracted_texts)} pieces")
        logger.info(f"Combined prompt: {combined_prompt[:100]}...")  # Log only first 100 chars

        # Step 3: Call LLM Prompt Service
        prompt_payload = {
            "prompt": combined_prompt,
            "temperature": float(request.query_params.get("temperature", 0.7)),
            "max_tokens": int(request.query_params.get("max_tokens", 500))
        }

        logger.info("Sending prompt to LLM Prompt Service")
        llm_response = requests.post(f"{LLM_PROMPT_SERVICE_URL}/generate", json=prompt_payload)
        llm_response.raise_for_status()

        return llm_response.json()

    except Exception as e:
        logger.exception(f"Error in /query: {e}")
        raise HTTPException(status_code=500, detail="Failed to process the combined query")


@app.get("/promptQuery")
async def prompt_query(request: Request):
    prompt_text = request.query_params.get("prompt")
    if not prompt_text:
        raise HTTPException(status_code=400, detail="Query parameter 'prompt' is required.")

    payload = {
        "prompt": prompt_text,
        "temperature": float(request.query_params.get("temperature", 0.7)),
        "max_tokens": int(request.query_params.get("max_tokens", 500))
    }

    try:
        logger.info(f"Forwarding prompt to LLM Prompt Service: {payload}")
        response = requests.post(f"{LLM_PROMPT_SERVICE_URL}/generate", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error in /promptQuery: {e}")
        raise HTTPException(status_code=500, detail="Failed to query Prompt Service.")

@app.post("/store")
def store_documents(request: StoreRequest):
    try:
        logger.info(f"Fetching S3 URIs for session_id: {request.session_id}")
        s3_uris = get_s3_uris(request.session_id)
        logger.info(f"Found {len(s3_uris)} S3 URIs for session_id: {request.session_id}")
        logger.info(f"Request payload: {s3_uris}")
        if not s3_uris:
            raise HTTPException(status_code=404, detail="No documents found in S3 for this session_id")

        payload_to_extractor = {
            "documents": s3_uris
        }
        if request.yt_list:
            payload_to_extractor["youtube_videos"] = request.yt_list

        logger.info(f"Calling ExtractorService with {len(s3_uris)} S3 URIs -->{payload_to_extractor}")
        extractor_response = requests.post(
            f"{EXTRACTOR_SERVICE_URL}/process",
            json=payload_to_extractor
        )
        logger.info(f"ExtractorService response: {extractor_response.status_code}")
        extractor_response.raise_for_status()
        processed_data = extractor_response.json()

        # Transforming processed data into DBService format
        db_request_payload = {
            "documents": [],
            "tag": request.tag,
            "session_id": request.session_id
        }

        for uri, chunks in processed_data.items():
            doc = {
                "uri": uri,
                "video_id": "",  # you can enhance this if needed
                "chunks": [{"chunk_id": idx, "text": text} for idx, text in enumerate(chunks)]
            }
            db_request_payload["documents"].append(doc)
        logger.info(f"Transformed data for DBService: {db_request_payload}")
        logger.info(f"Sending {len(db_request_payload['documents'])} documents to DBService")

        db_response = requests.post(
            f"{DB_SERVICE_URL}/store",
            json=db_request_payload
        )
        db_response.raise_for_status()

        return {"message": "Documents stored successfully"}

    except Exception as e:
        logger.exception("Failed during /store process")
        raise HTTPException(status_code=500, detail=str(e))


# Health Check
@app.get("/health")
async def health_check():
    return {"status": "Backend Service is healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
    logger.info("Starting DB Service...")
    logger.info("DB Service started successfully.")
