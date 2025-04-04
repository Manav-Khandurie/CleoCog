import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mangum import Mangum

# LLM imports
from langchain_openai import ChatOpenAI  # Reusing OpenAI-compatible client
from langchain_community.chat_models import ChatOpenAI, ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # Ignore if dotenv is not installed in Lambda


def get_env_var(name: str, default: Optional[str] = None) -> str:
    """Retrieve environment variables safely for both local and AWS Lambda environments."""
    return os.environ.get(name, default)

class LLMRequest(BaseModel):
    prompt: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500

class LLMResponse(BaseModel):
    generated_text: str

app = FastAPI()
handler = Mangum(app)

def get_llm():
    llm_provider = get_env_var("LLM_PROVIDER", "openai").lower()
    
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
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")

@app.post("/generate", response_model=LLMResponse)
async def generate_text(request: LLMRequest):
    try:
        llm = get_llm()
        response = await llm.ainvoke(request.prompt)
        return {"generated_text": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# import json
# import uuid
# import boto3

# def lambda_handler(event, context):
#     try:
#         uuid_value = str(uuid.uuid4())

#         return {
#             'statusCode': 200,
#             'body': json.dumps({'message': 'Data saved successfully' , 'uuid': uuid_value})
#         }
#     except Exception as e:
#         return {
#             'statusCode': 500,
#             'body': json.dumps({'message': f'Error saving data to DynamoDB: {str(e)}'})
#         }
