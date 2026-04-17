from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    PROJECT_NAME: str = "EpicCV AI Backend"

    class Config:
        env_file = ".env"

settings = Settings()