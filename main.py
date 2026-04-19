from fastapi import FastAPI
from app.api.endpoints import router as ai_router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
# --- CẤU HÌNH CORS TẠI ĐÂY ---
origins = [
    "http://localhost:3000",    # URL của ứng dụng React/Next.js
    "http://127.0.0.1:3000",
    "http://localhost:8000",    # Cho phép chính nó (thử nghiệm Swagger)
    "*",                        # Cho phép TẤT CẢ (chỉ dùng khi phát triển, không dùng khi deploy thật)
]



app.include_router(ai_router, prefix="/ai")