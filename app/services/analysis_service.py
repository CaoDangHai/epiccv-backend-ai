import yaml
import os
import logging
from dotenv import load_dotenv
from fastapi import HTTPException
from pydantic import ValidationError
from langchain_core.exceptions import OutputParserException
from langchain_openai import ChatOpenAI

# Import your schemas
from app.schemas.result import ComparisonAnalysisResponse
from app.schemas.cv import FilteredCVResponse
from app.schemas.jd import JDResponse 
from app.core.llm import LLMFactory

logger = logging.getLogger("uvicorn.error")
load_dotenv()

class AnalysisService:
    def __init__(self):
        # 1. Initialize LLM with Structured Output
        
        self.llm = LLMFactory.get_model("gpt-4.1-mini") #
        self.structured_llm = self.llm.with_structured_output(ComparisonAnalysisResponse, method="function_calling")

        # 2. Load the System Prompt from YAML
        self.system_message = self._load_system_prompt()
 
    def _load_system_prompt(self) -> str:
        """Reads and formats the analysis logic from YAML"""
        try:
            prompt_path = os.path.join("app", "prompts", "analysis_prompt1.yaml")
            with open(prompt_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            config = data["analysis_logic"]
            full_prompt = "SYSTEM ROLE & OBJECTIVE:\n"
            
            # Efficiently parsing the YAML structure into a text prompt
            for key, value in config.items():
                if isinstance(value, list):
                    content = "\n".join([f"- {item}" for item in value])
                elif isinstance(value, dict):
                    content = "\n".join([f"- {k}: {v}" for k, v in value.items()])
                else:
                    content = str(value)
                full_prompt += f"\n{key.upper()}:\n{content}\n"
                
            return full_prompt
        except Exception as e:
            logger.error(f"Error loading Analysis YAML: {e}")
            return "Compare the provided CV and JD. Output a structured analysis."

    async def compare_cv_with_jd(self, cv_data: FilteredCVResponse, jd_data: JDResponse) -> ComparisonAnalysisResponse:
        """
        Performs the deep-dive analysis between candidate and job.
        """
        try:
            # Prepare the human message with both data sources
            # Using model_dump_json ensures clean data transfer to the LLM
            human_message = f"""
            PROCESS THIS CANDIDATE VS JOB:
            ---
            CANDIDATE (Filtered CV):
            {cv_data.model_dump_json(indent=2)}
            
            ---
            JOB DESCRIPTION (Filtered JD):
            {jd_data.model_dump_json(indent=2)}
            """

            result = await self.structured_llm.ainvoke([
                ("system", self.system_message),
                ("human", human_message)
            ])
            
            return result

        except ValidationError as ve:
            logger.warning(f"Analysis Validation Error: {str(ve)}")
            raise HTTPException(
                status_code=422, 
                detail="Dữ liệu phân tích trả về không đúng cấu trúc ComparisonAnalysisResponse."
            )

        except OutputParserException as ope:    
            logger.warning(f"Analysis Parsing Error: {str(ope)}")
            raise HTTPException(
                status_code=400, 
                detail="AI gặp lỗi khi bóc tách kết quả so sánh."
            )

        except Exception as e:
            logger.error(f"System error in AnalysisService: {str(e)}")
            if any(code in str(e) for code in ["401", "403"]):
                raise HTTPException(status_code=500, detail="Lỗi API Key !")
            raise HTTPException(status_code=500, detail="Hệ thống phân tích đang 'bận', thử lại sau nhé!")

# Instantiate for use in routers
analysis_service = AnalysisService()