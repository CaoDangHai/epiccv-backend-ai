import logging
import os

import yaml
from dotenv import load_dotenv
from fastapi import HTTPException
from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError

from app.core.llm import LLMFactory, ainvoke_structured_with_retry
from app.schemas.result import ComparisonAnalysisResponse
from app.schemas.roadmap import LearningRoadmapResponse

logger = logging.getLogger("uvicorn.error")
load_dotenv()


class RoadmapService:
    def __init__(self):
        self.llm = LLMFactory.get_model("gpt-4.1")
        self.structured_llm = self.llm.with_structured_output(
            LearningRoadmapResponse,
            method="function_calling",
        )
        self.system_message = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        try:
            prompt_path = os.path.join("app", "prompts", "gen_roadmap2.yaml")
            with open(prompt_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            config = data["roadmap_generation_logic"]
            full_prompt = "SYSTEM ROLE & OBJECTIVE:\n"

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
            logger.error(f"Error loading roadmap YAML: {e}")
            return "Generate a learning roadmap based on the CV and JD analysis."

    async def generate_roadmap(
        self,
        result_data: ComparisonAnalysisResponse,
    ) -> LearningRoadmapResponse:
        try:
            human_message = f"Comparison Result:\n{result_data.model_dump_json()}"
            return await ainvoke_structured_with_retry(
                self.structured_llm,
                [
                    ("system", self.system_message),
                    ("human", human_message),
                ],
                "Roadmap generation",
            )
        except (ValidationError, OutputParserException) as e:
            logger.error(f"Output parsing error in roadmap generation: {e}")
            raise HTTPException(status_code=500, detail=f"Roadmap output parsing failed: {str(e)}")
        except Exception as e:
            logger.error(f"General error in roadmap generation: {e}")
            raise HTTPException(status_code=500, detail=f"Roadmap generation failed: {str(e)}")


roadmap_service = RoadmapService()
