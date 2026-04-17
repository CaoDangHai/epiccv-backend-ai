from fastapi import FastAPI
from app.core.config import settings
from app.services.ai_check import init_ai_components

app = FastAPI(title=settings.PROJECT_NAME)

@app.on_event("startup")
async def startup_event():
    init_ai_components()

@app.get("/")
def read_root():
    return {"message": "Server đang chạy mượt mà!", "project": settings.PROJECT_NAME}


