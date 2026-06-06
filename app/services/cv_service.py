import json
import logging
import os

import yaml
from dotenv import load_dotenv
from fastapi import HTTPException
from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError

from app.core.llm import LLMFactory
from app.schemas.cv import CVResponse, FilteredCVResponse

logger = logging.getLogger("uvicorn.error")
load_dotenv()


class CvService:
    def __init__(self):
        self.llm = LLMFactory.get_model("gpt-4o-mini")
        self.structured_llm = self.llm.with_structured_output(
            CVResponse,
            method="function_calling",
        )
        self.system_message = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        try:
            prompt_path = os.path.join("app", "prompts", "extract_cv_prompt2.yaml")
            with open(prompt_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            config = data["cv_extraction"]
            full_prompt = ""
            for key, value in config.items():
                if isinstance(value, list):
                    content = "\n".join([f"- {item}" for item in value])
                elif isinstance(value, dict):
                    content = "\n".join([f"- {k}: {v}" for k, v in value.items()])
                else:
                    content = str(value)
                full_prompt += f"{key.upper()}:\n{content}\n\n"

            return full_prompt
        except Exception as e:
            logger.error(f"Unable to load CV prompt YAML: {e}")
            return "You are an expert ATS data extraction AI. Extract CV precisely."

    async def _invoke_structured_output(self, raw_text: str) -> CVResponse:
        for attempt in range(2):
            result = await self.structured_llm.ainvoke([
                ("system", self.system_message),
                ("human", raw_text),
            ])
            if result is not None:
                return result
            logger.warning("CV extraction returned no structured output on attempt %s", attempt + 1)

        raise HTTPException(status_code=502, detail="AI did not return a CV extraction result.")

    async def extract_cv_data(self, raw_text: str) -> CVResponse:
        logger.info(f"Received CV text length: {len(raw_text)} characters")
        try:
            result = await self._invoke_structured_output(raw_text)
            pretty_output = json.dumps(result.model_dump(), indent=2, ensure_ascii=False)
            logger.info("Parsed CV data:\n" + pretty_output)
            return result
        except ValidationError as ve:
            logger.warning(f"CV validation error: {str(ve)}")
            raise HTTPException(
                status_code=422,
                detail="Extracted CV data does not match the required structure.",
            )

        except OutputParserException as ope:
            logger.warning(f"CV output parsing error: {str(ope)}")
            raise HTTPException(
                status_code=400,
                detail="AI returned an invalid CV extraction format.",
            )

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"System error in CvService: {str(e)}")
            if any(code in str(e) for code in ["401", "403", "invalid_api_key"]):
                raise HTTPException(status_code=500, detail="Invalid or unauthorized API key.")
            raise HTTPException(status_code=500, detail="CV extraction service is busy. Please try again later.")

    def filter_cv_data(self, cv_data: CVResponse) -> FilteredCVResponse:
        return cv_data.to_filtered()


cv_service = CvService()
