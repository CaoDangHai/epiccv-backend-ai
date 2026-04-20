import yaml
import os
import logging
from dotenv import load_dotenv 
from fastapi import HTTPException
from pydantic import ValidationError
from langchain_core.exceptions import OutputParserException
from app.schemas.jd import JDResponse 
from app.core.llm import LLMFactory

# Khởi tạo logger 
logger = logging.getLogger("uvicorn.error")

load_dotenv() 

class JdService:
    def __init__(self):
        # 1. Khởi tạo LLM 
       
        self.llm = LLMFactory.get_model("gemini-2.5-flash") 
        self.structured_llm = self.llm.with_structured_output(JDResponse)

        # 2. Load Prompt từ file YAML 
        self.system_message = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Đọc và format prompt"""
        try:
            # Đường dẫn đến file YAML trích xuất JD
            prompt_path = os.path.join("app", "prompts", "extract_jd_prompt1.yaml")
            
            if not os.path.exists(prompt_path):
                raise FileNotFoundError(f"Không tìm thấy file: {prompt_path}")

            with open(prompt_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            # Gom toàn bộ nội dung trong YAML (system_role, extraction_rules, etc.) thành 1 chuỗi
            full_prompt = ""
            for key, value in data.items():
                if isinstance(value, list):
                    content = "\n".join([f"- {item}" for item in value])
                elif isinstance(value, dict):
                    content = "\n".join([f"- {k}: {v}" for k, v in value.items()])
                else:
                    content = str(value)
                full_prompt += f"{key.upper()}:\n{content}\n\n"
                
            return full_prompt
            
        except Exception as e:
            logger.error(f"Lỗi khi load YAML JD: {e}")
            # Fallback prompt tối giản
            return "You are an expert Technical Recruiter. Extract Job Description details accurately into the requested JSON format."

    async def extract_jd_data(self, raw_text: str) -> JDResponse:
        """Hàm chính gọi AI để xử lý văn bản JD thô"""
        try:
            # Gọi Gemini xử lý structured output
            result = await self.structured_llm.ainvoke([
                ("system", self.system_message),
                ("human", raw_text)
            ])
            return result

        except ValidationError as ve:
            logger.warning(f"JD Validation error: {str(ve)}")
            raise HTTPException(
                status_code=422, 
                detail="Dữ liệu JD do AI trả về không khớp với cấu trúc hệ thống."
            )

        except OutputParserException as ope:    
            logger.warning(f"JD Output parsing error: {str(ope)}")
            raise HTTPException(
                status_code=400, 
                detail="AI phản hồi sai định dạng kỹ thuật khi xử lý JD."
            )

        except Exception as e:
            logger.error(f"Lỗi hệ thống khi trích xuất JD: {str(e)}")
            if "401" in str(e) or "403" in str(e):
                raise HTTPException(status_code=500, detail="API Key Google (JD Service) có vấn đề!")
            raise HTTPException(status_code=500, detail="Hệ thống AI đang gặp sự cố khi đọc JD.")


jd_service = JdService()