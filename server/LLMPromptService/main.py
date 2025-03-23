# app/main.py
import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mangum import Mangum

# LLM imports
from langchain_openai import ChatOpenAI  # Reusing OpenAI-compatible client
from langchain_community.llms import OpenAI
from langchain_community.chat_models import ChatOpenAI, ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()  # Loads variables from .env file
class LLMRequest(BaseModel):
    prompt: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500

class LLMResponse(BaseModel):
    generated_text: str

app = FastAPI()
handler = Mangum(app)

def get_llm():
    llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if llm_provider == "openai":
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            temperature=0.7,
            max_tokens=500
        )
    elif llm_provider == "anthropic":
        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-2"),
            temperature=0.7,
            max_tokens=500
        )
    elif llm_provider == "google":
        return ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_MODEL", "gemini-pro"),
            temperature=0.7
        )
    elif llm_provider == "bedrock":
        return Bedrock(
            model_id=os.getenv("BEDROCK_MODEL", "anthropic.claude-v2"),
            region_name=os.getenv("AWS_REGION", "us-west-2"),
            temperature=0.7,
            max_tokens_to_sample=500
        )
    elif llm_provider == "deepseek":
        return ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            openai_api_base=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"),
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
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