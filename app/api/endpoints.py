from fastapi import APIRouter, UploadFile, File, HTTPException
# Import trực tiếp instance đã tạo sẵn từ file service
from app.services.cv_service import cv_service 
from app.services.jd_service import jd_service
from app.schemas.jd import JDResponse
from app.schemas.cv import CVResponse
import logging
    

logger = logging.getLogger("uvicorn.error")
router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "message": "EpicCV AI Engine is active!"}

@router.post("/extract-cv", response_model=CVResponse)
async def extract_cv(file: UploadFile = File(...)):
    try:
        # Đọc file
        content = await file.read()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Vui lòng upload file text định dạng UTF-8.")

        if not text.strip():
            raise HTTPException(status_code=400, detail="CV không có nội dung để phân tích.")

        
        cv_data = await cv_service.extract_cv_data(text)

        return cv_data

    except Exception as e:
        logger.error(f"Lỗi tại Endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý: {str(e)}")
    

@router.post("/extract-jd", response_model=JDResponse)
async def extract_jd(file: UploadFile = File(None), jd_text: str = None):
    """
    Endpoint trích xuất thông tin JD. 
    Hỗ trợ cả upload file (.txt) hoặc dán text trực tiếp.
    """
    try:
        text = ""
        
        # 1. Ưu tiên xử lý file nếu có upload
        if file:
            content = await file.read()
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="Vui lòng upload file text định dạng UTF-8.")
        
        # 2. Nếu không có file thì lấy từ field jd_text (cho trường hợp paste text từ UI)
        elif jd_text:
            text = jd_text
            
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Nội dung JD không được để trống.")

        # 3. Gọi service xử lý trích xuất (Sử dụng Prompt YAML English đã tạo trước đó)
        jd_data = await jd_service.extract_jd_data(text)

        return jd_data

    except Exception as e:
        logger.error(f"Lỗi tại Endpoint JD: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý trích xuất JD: {str(e)}")