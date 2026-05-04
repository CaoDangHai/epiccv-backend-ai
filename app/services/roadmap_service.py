import yaml
import os
import logging
from dotenv import load_dotenv 
from fastapi import HTTPException
from pydantic import ValidationError
from langchain_core.exceptions import OutputParserException
from app.schemas.result import ComparisonAnalysisResponse
from app.schemas.roadmap import LearningRoadmapResponse
from app.core.llm import LLMFactory
from app.schemas.cv import FilteredCVResponse
from app.schemas.jd import JDResponse

logger = logging.getLogger("uvicorn.error")

load_dotenv()

class RoadmapService:
    def __init__(self):
        # 1. Initialize LLM with Structured Output
        self.llm = LLMFactory.get_model("gpt-4.1-mini") #
        self.structured_llm = self.llm.with_structured_output(LearningRoadmapResponse, method="function_calling")

        # 2. Load the System Prompt from YAML
        self.system_message = self._load_system_prompt()
 
    def _load_system_prompt(self) -> str:
        """Reads and formats the roadmap generation logic from YAML"""
        try:
            prompt_path = os.path.join("app", "prompts", "gen_roadmap2.yaml")
            with open(prompt_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            config = data["roadmap_generation_logic"]
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
            logger.error(f"Error loading Roadmap YAML: {e}")
            return "Generate a learning roadmap based on the CV and JD analysis."
    
    async def generate_roadmap(self, result_data: ComparisonAnalysisResponse) -> LearningRoadmapResponse:
        """
        Generates a personalized learning roadmap for the candidate based on the CV and JD analysis.
        """
        try:
            
            human_message = f"Comparison Result:\n{result_data.model_dump_json()}"
            
            result = await self.structured_llm.ainvoke([
                ("system", self.system_message),
                ("human", human_message)    
            ])
            return result
        except (ValidationError, OutputParserException) as e:
            logger.error(f"Output parsing error in Roadmap generation: {e}")
            raise HTTPException(status_code=500, detail=f"Lỗi phân tích kết quả tạo lộ trình: {str(e)}")
        except Exception as e:
            logger.error(f"General error in Roadmap generation: {e}")
            raise HTTPException(status_code=500, detail=f"Lỗi xử lý tạo lộ trình: {str(e)}")
        

roadmap_service = RoadmapService()