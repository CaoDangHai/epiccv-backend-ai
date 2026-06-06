import logging

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.schemas.result import ComparisonAnalysisResponse
from app.schemas.roadmap import LearningRoadmapResponse
from app.services.roadmap_service import roadmap_service
from app.services.analysis_service import analysis_service
from app.services.cv_service import cv_service
from app.services.jd_service import jd_service
from app.schemas.jd import JDResponse
from app.schemas.cv import CVResponse, FilteredCVResponse

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok", "message": "EpicCV AI Engine is active!"}


@router.post("/extract-cv", response_model=CVResponse)
async def extract_cv(file: UploadFile = File(...)):
    try:
        content = await file.read()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Please upload a UTF-8 text file.")

        if not text.strip():
            raise HTTPException(status_code=400, detail="CV content is empty.")

        cv_data = await cv_service.extract_cv_data(text)
        if cv_data is None:
            raise HTTPException(status_code=500, detail="LLM did not return a valid result.")

        return cv_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV extraction endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CV extraction failed: {str(e)}")


@router.post("/extract-jd", response_model=JDResponse)
async def extract_jd(file: UploadFile = File(None), jd_text: str = None):
    try:
        text = ""
        if file:
            content = await file.read()
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="Please upload a UTF-8 text file.")
        elif jd_text:
            text = jd_text

        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Job description content cannot be empty.")

        return await jd_service.extract_jd_data(text)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JD extraction endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"JD extraction failed: {str(e)}")


@router.post("/compare", response_model=ComparisonAnalysisResponse)
async def compare_cv_jd(cv_data: FilteredCVResponse, jd_data: JDResponse):
    try:
        return await analysis_service.compare_cv_with_jd(cv_data, jd_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compare endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.post("/generate-roadmap", response_model=LearningRoadmapResponse)
async def generate_roadmap(result_data: ComparisonAnalysisResponse):
    try:
        return await roadmap_service.generate_roadmap(result_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate roadmap endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Roadmap generation failed: {str(e)}")


@router.post("/full-pipeline")
async def full_analysis_pipeline(cv_file: UploadFile = File(...), jd_file: UploadFile = File(...)):
    try:
        cv_content = await cv_file.read()
        raw_cv_text = cv_content.decode("utf-8")
        full_cv = await cv_service.extract_cv_data(raw_cv_text)
        filtered_cv = full_cv.to_filtered()

        jd_content = await jd_file.read()
        raw_jd_text = jd_content.decode("utf-8")
        jd_data = await jd_service.extract_jd_data(raw_jd_text)

        analysis_result = await analysis_service.compare_cv_with_jd(filtered_cv, jd_data)
        roadmap = await roadmap_service.generate_roadmap(analysis_result)

        return {
            "full_cv": full_cv.model_dump(),
            **analysis_result.model_dump(by_alias=True),
            "roadmap": roadmap.model_dump(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Full pipeline endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Full pipeline failed: {str(e)}")
