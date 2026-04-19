from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):

    GEMINI_KEY: str = Field(..., alias="GEMINI_KEY")

    DATABASE_URL: str
    PROJECT_NAME: str = "EpicCV AI Backend"

    class Config:
        env_file = ".env"

settings = Settings()