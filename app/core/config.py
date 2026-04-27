from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):

    GOOGLE_KEY: str = Field(..., alias="GOOGLE_KEY")
    TROLLLM_KEY: str = Field(..., alias="TROLLLM_KEY")
    DATABASE_URL: str
    PROJECT_NAME: str = "EpicCV AI Backend"
    

    class Config:
        env_file = ".env"

settings = Settings()