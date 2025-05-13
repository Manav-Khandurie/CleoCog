from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"


settings = Settings()
