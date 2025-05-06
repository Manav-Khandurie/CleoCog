import os
import logging
import requests
import uvicorn
import json
import boto3
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List
from typing import Optional
from fastapi import UploadFile, File
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError 
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

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)
class StoreRequest(BaseModel):
    session_id: str
    tag: str
    yt_list: Optional[List[str]] = None
class UploadRequest(BaseModel):
    session_id: str
    filenames: List[str]

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

def calculate_k_from_chunks(
    total_chunks: int, 
    default_k: int = 5, 
    max_k: int = 10, 
    percentage: float = 0.2
) -> int:
    """
    Dynamically calculate how many chunks to retrieve, based on available chunks.

    Args:
    - chunk_list (list): List of chunks (retrieved from DB or candidate set).
    - default_k (int): Default number of chunks.
    - max_k (int): Maximum number of chunks.
    - percentage (float): Percentage of available chunks to retrieve.

    Returns:
    - int: number of chunks to retrieve.
    """

    if total_chunks == 0:
        return 0  # Nothing to retrieve
    
    percentage_k = int(total_chunks * percentage)
    k = max(default_k, percentage_k)
    k = min(k, max_k)
    k = min(k, total_chunks)  # never more than available chunks
    return k

def get_k(session_id: str, tag: str) -> int:
    try:
        # Make the GET request to fetch the value of k
        response = requests.get(f"{DB_SERVICE_URL}/totalChunks", params={ "session_id": session_id, "tag": tag })
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()
        logger.info(f"Response from DBService for K: {data}")
        total_chunks = data.get("total", 5)  # Default to 5 if the key is not present
        k=  calculate_k_from_chunks(total_chunks)
        logger.info(f"Calculated K: {k} based on total chunks: {total_chunks}") 
        # Ensure k is a positive integer
        if not isinstance(k, int) or k <= 0:
            logger.warning(f"Invalid value for K: {k}. Defaulting to 5.")
            k = 5
        
        return k
    except (requests.RequestException, ValueError) as e:
        # Catch errors related to the HTTP request or invalid JSON parsing
        logger.error(f"Error in get_k: {e}")
        return 5

# ----------------- API Endpoints -----------------
@app.get("/")
async def root():
    return {"message": "Welcome to the Backend Service"}

@app.get("/databaseQuery")
async def query(request: Request):
    query_text = request.query_params.get("query")
    if not query_text:
        raise HTTPException(status_code=400, detail="Query parameter 'query' is required.")
    session_id = request.query_params.get("session_id", "")
    tag = request.query_params.get("tag", "")
    top_k= get_k(session_id, tag)
    payload = {
        "query": query_text,
        "tag": tag,
        "session_id": session_id,
        "top_k": top_k
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
    session_id = request.query_params.get("session_id", "")
    tag = request.query_params.get("tag", "")
    top_k= get_k(session_id, tag)
    logger.info(f"Top K: {top_k}") 
    db_payload = {
        "query": query_text,
        "tag": tag,
        "session_id": session_id,
        "top_k": top_k
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
        logger.info("-------------------------------------------------")
        logger.info("-------------------------------------------------")
        logger.info("-------------------------------------------------")
        logger.info(f"DB response: {db_data}")
        logger.info("-------------------------------------------------")
        logger.info("-------------------------------------------------")
        logger.info("-------------------------------------------------")
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
        Ensure that you response is relevant to the text provided and does not include any unrelated information.
        If the information is not sufficient to answer the question, please indicate that.
        And only give response in text fromat no other formata and no highlights,bolds etc.
        """

        logger.info(f"Combined prompt text prepared with {len(extracted_texts)} pieces")
        logger.info(f"Combined prompt: {combined_prompt[:500]}...")  # Log only first 100 chars

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

@app.get("/createSession")
async def create_session():
    try:
        session_id = str(uuid.uuid4())
        bucket = os.getenv("S3_BUCKET_NAME")
        folder_key = f"{session_id}/"

        # Create folder by uploading an empty object
        s3_client.put_object(Bucket=bucket, Key=folder_key)
        logger.info(f"Created S3 folder for session: {session_id}")

        return {"session_id": session_id}
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")

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
        
        logger.info("-------------------------------------------------")
        logger.info(f"Payload to ExtractorService: {payload_to_extractor}")
        logger.info("-------------------------------------------------")
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
            "session_id": request.session_id,
            "tag": request.tag,
            "documents": []
        }

        # Process document chunks from ExtractorService response
        for doc_chunk in processed_data.get("document_chunks", []):
            doc = {
                "uri": doc_chunk["s3_uri"],
                "chunks": [{"chunk_id": idx, "text": text} for idx, text in enumerate(doc_chunk["chunks"])]
            }
            db_request_payload["documents"].append(doc)

        # Process YouTube chunks if any (though the example shows empty youtube_chunks)
        for yt_chunk in processed_data.get("youtube_chunks", []):
            doc = {
                "video_id": yt_chunk["video_id"],  # Assuming this field exists in the response
                "chunks": [{"chunk_id": idx, "text": text} for idx, text in enumerate(yt_chunk["chunks"])]
            }
            db_request_payload["documents"].append(doc)

        logger.info(f"Transformed data for DBService: {db_request_payload}")
        logger.info(f"Sending {len(db_request_payload['documents'])} documents to DBService")
        logger.info("-------------------------------------------------")
        logger.info(f"DB request payload: {db_request_payload}")
        logger.info("-------------------------------------------------")
        
        db_response = requests.post(
            f"{DB_SERVICE_URL}/store",
            json=db_request_payload
        )
        db_response.raise_for_status()

        return {"message": "Documents stored successfully"}

    except Exception as e:
        logger.exception("Failed during /store process")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/uploadDocs")
def get_presigned_urls(req: UploadRequest):
    try:
        bucket = os.getenv("S3_BUCKET_NAME")
        urls = {}

        for name in req.filenames:
            key = f"{req.session_id}/{name}"
            url = s3_client.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    'Bucket': bucket,
                    'Key': key,
                    'ContentType': 'application/pdf'  # match the upload
                },
                ExpiresIn=3600,
                HttpMethod='PUT'  # very important!
            )
            urls[name] = url

        return {"presigned_urls": urls}

    except ClientError as e:
        logger.error(f"Error generating presigned URLs: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate upload URLs")
    
# Health Check
@app.get("/health")
async def health_check():
    return {"status": "Backend Service is healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
    logger.info("Starting DB Service...")
    logger.info("DB Service started successfully.")
