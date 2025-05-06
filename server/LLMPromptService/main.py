import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mangum import Mangum

# LLM imports
from langchain_openai import ChatOpenAI  # Reusing OpenAI-compatible client
from langchain_community.chat_models import ChatOpenAI, ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI



# Load environment variables in local development
if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not installed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_env_var(name: str, default: Optional[str] = None) -> str:
    """Retrieve environment variables safely for both local and AWS Lambda environments."""
    value = os.environ.get(name, default)
    logger.debug(f"Environment variable {name} resolved to: {value}")
    return value

class LLMRequest(BaseModel):
    prompt: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500

class LLMResponse(BaseModel):
    generated_text: str

app = FastAPI()
handler = Mangum(app)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)
def get_llm():
    llm_provider = get_env_var("LLM_PROVIDER", "openai").lower()
    logger.info(f"Initializing LLM provider: {llm_provider}")

    if llm_provider == "openai":
        return ChatOpenAI(
            model=get_env_var("OPENAI_MODEL", "gpt-3.5-turbo"),
            temperature=0.7,
            max_tokens=500
        )
    elif llm_provider == "anthropic":
        return ChatAnthropic(
            model=get_env_var("ANTHROPIC_MODEL", "claude-2"),
            temperature=0.7,
            max_tokens=500
        )
    elif llm_provider == "google":
        return ChatGoogleGenerativeAI(
            model=get_env_var("GOOGLE_MODEL", "gemini-pro"),
            temperature=0.7
        )
    elif llm_provider == "bedrock":
        return Bedrock(
            model_id=get_env_var("BEDROCK_MODEL", "anthropic.claude-v2"),
            region_name=get_env_var("AWS_REGION", "us-west-2"),
            temperature=0.7,
            max_tokens_to_sample=500
        )
    elif llm_provider == "deepseek":
        return ChatOpenAI(
            model=get_env_var("DEEPSEEK_MODEL", "deepseek-chat"),
            openai_api_base=get_env_var("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"),
            openai_api_key=get_env_var("DEEPSEEK_API_KEY"),
            temperature=0.7,
            max_tokens=500
        )
    else:
        logger.error(f"Unsupported LLM provider: {llm_provider}")
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")

@app.post("/generate", response_model=LLMResponse)
async def generate_text(request: LLMRequest):
    logger.info(f"Received generation request with prompt: {request.prompt[:100]}...")  # Log only first 100 chars

    try:
        llm = get_llm()
        response = await llm.ainvoke(request.prompt)
        logger.info(f"Generated text successfully")
        return {"generated_text": response.content}
    except Exception as e:
        logger.exception("Failed to generate text")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting development server")
    uvicorn.run(app, host="0.0.0.0", port=8002)

# Example of enhanced Lambda handler logging
# import json
# import uuid
# import boto3

# def lambda_handler(event, context):
#     logger.info("Lambda function invoked")
#     try:
#         uuid_value = str(uuid.uuid4())
#         logger.info(f"Generated UUID: {uuid_value}")

#         return {
#             'statusCode': 200,
#             'body': json.dumps({'message': 'Data saved successfully', 'uuid': uuid_value})
#         }
#     except Exception as e:
#         logger.exception("Error saving data to DynamoDB")
#         return {
#             'statusCode': 500,
#             'body': json.dumps({'message': f'Error saving data to DynamoDB: {str(e)}'})
#         }
