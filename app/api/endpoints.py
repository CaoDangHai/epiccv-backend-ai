from fastapi import APIRouter, Body, UploadFile, File, HTTPException
# Import trực tiếp instance đã tạo sẵn từ file service
from app.schemas.result import ComparisonAnalysisResponse
from app.schemas.roadmap import LearningRoadmapResponse
from app.services import roadmap_service
from app.services.analysis_service import analysis_service
from app.services.cv_service import cv_service 
from app.services.jd_service import jd_service
from app.schemas.jd import JDResponse
from app.schemas.cv import CVResponse, FilteredCVResponse
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

        if cv_data is None:
            # Nếu service trả về None, phải báo lỗi ngay
            raise HTTPException(
                status_code=500,
                detail="LLM không trả về kết quả hợp lệ."
            )

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
    
@router.post("/compare", response_model=ComparisonAnalysisResponse)
async def compare_cv_jd(cv_data: FilteredCVResponse, jd_data: JDResponse):
    try:
        result = await analysis_service.compare_cv_with_jd(cv_data, jd_data)
        return result
    except Exception as e:
        logger.error(f"Lỗi tại Endpoint Compare: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý so sánh: {str(e)}"    )
    

@router.post("/generate-roadmap",response_model= LearningRoadmapResponse)
async def generate_roadmap(cv_data: FilteredCVResponse, jd_data: JDResponse):
    try:
        roadmap = await roadmap_service.generate_roadmap(cv_data, jd_data)
        return roadmap
    except Exception as e:
        logger.error(f"Lỗi tại Endpoint Generate Roadmap: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý tạo lộ trình: {str(e)}")

@router.post("/full-pipeline")
async def full_analysis_pipeline(cv_file: UploadFile = File(...), jd_file: UploadFile = File(...)):
    # Bước 1: Trích xuất CV đầy đủ (Full CV)
    cv_content = await cv_file.read()
    raw_cv_text = cv_content.decode("utf-8")
    full_cv = await cv_service.extract_cv_data(raw_cv_text) # Trả về CVResponse

    # Bước 2: Biến đổi thành Filtered CV (Lọc PII)

    filtered_cv = full_cv.to_filtered() # Trả về FilteredCVResponse, đã lọc PII và chỉ giữ lại phần cần thiết cho phân tích và tạo roadmap

    # Bước 3: Trích xuất JD
    jd_content = await jd_file.read()
    raw_jd_text = jd_content.decode("utf-8")
    jd_data = await jd_service.extract_jd_data(raw_jd_text) # Trả về JDResponse


    # Bước 4: Truyền vào Analysis Service để đối chiếu
    analysis_result = await analysis_service.compare_cv_with_jd(filtered_cv, jd_data) #

    return {
        "full_cv": full_cv, # Trả về để hiện trên UI cho user sửa nếu cần
        "analysis": analysis_result
    }