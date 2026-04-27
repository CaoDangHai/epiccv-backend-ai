import yaml
import os
import logging
from dotenv import load_dotenv 
from fastapi import HTTPException
from pydantic import ValidationError
from langchain_core.exceptions import OutputParserException
from app.schemas.cv import CVResponse
from app.core.llm import LLMFactory

# Khởi tạo logger 
logger = logging.getLogger("uvicorn.error")



load_dotenv() # đọc file .env vào hệ thống

class CvService:
    def __init__(self):
        # 1. Khởi tạo LLM
        self.llm = LLMFactory.get_model("gemini-2.5-flash") #
        self.structured_llm = self.llm.with_structured_output(CVResponse)
    
        # 2. Tách Prompt: Load từ file YAML
        self.system_message = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Hàm phụ trợ để đọc và format prompt từ YAML"""
        try:
            # Đường dẫn tìm đến file YAML trong folder core
            prompt_path = os.path.join("app", "prompts", "extract_cv_prompt1.yaml")
            with open(prompt_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            config = data["cv_extraction"]
            
            # Gom các mảnh từ YAML lại thành 1 chuỗi hoàn chỉnh
            full_prompt =  ""
            for key, value in config.items():
                if (isinstance(value, list)):
                    content = "\n".join([f"- {item}" for item in value])
                elif isinstance(value, dict):
                    # Xử lý các mục con như strict_rules
                    content = "\n".join([f"- {k}: {v}" for k, v in value.items()])
                else:
                    content = str(value)
                full_prompt += f"{key.upper()}:\n{content}\n\n"
                
            return full_prompt
        except Exception as e:
            logger.error(f"Không tìm thấy hoặc lỗi file YAML : {e}")
            # Fallback prompt nếu lỡ file YAML bị xóa/lỗi để app không sập
            return "You are an expert ATS data extraction AI. Extract CV precisely."

    async def extract_cv_data(self, raw_text: str) -> CVResponse:
    
        try:
            result = await self.structured_llm.ainvoke([
                ("system", self.system_message),
                ("human", raw_text)
            ])
            return result

        except ValidationError as ve:
            logger.warning(f"Dữ liệu AI trả về không khớp Schema: {str(ve)}")
            raise HTTPException(
                status_code=422, 
                detail="Dữ liệu CV không trích xuất đúng cấu trúc yêu cầu."
            )

        except OutputParserException as ope:    
            logger.warning(f"Lỗi parse kết quả từ LLM: {str(ope)}")
            raise HTTPException(
                status_code=400, 
                detail="AI phản hồi sai định dạng kỹ thuật."
            )

        except Exception as e:
            logger.error(f"Lỗi hệ thống tại CvService: {str(e)}")
            if any(code in str(e) for code in ["401", "403", "invalid_api_key"]):
                raise HTTPException(status_code=500, detail="Lỗi xác thực API Key!")
            raise HTTPException(status_code=500, detail="Hệ thống AI đang bận, vui lòng thử lại sau!")
        
# Tạo instance
cv_service = CvService()
