from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):

    GOOGLE_KEY: str = Field(..., alias="GOOGLE_KEY")
    TROLLLM_KEY: str = Field(..., alias="TROLLLM_KEY")
    DATABASE_URL: str
    PROJECT_NAME: str = "EpicCV AI Backend"
    LLM_BASE_URL: str = Field(..., alias="LLM_BASE_URL")
    LLM_API_KEY: str = Field(..., alias="LLM_API_KEY")

    YES_SCALE_API_KEY: str = Field(..., alias="YES_SCALE_API_KEY")
    YES_SCALE_BASE_URL: str = Field(..., alias="YES_SCALE_BASE_URL")
    

    class Config:
        env_file = ".env"

settings = Settings()