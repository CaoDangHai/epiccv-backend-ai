import json
import logging
import os

import yaml
from dotenv import load_dotenv
from fastapi import HTTPException
from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError

from app.core.llm import LLMFactory
from app.schemas.jd import JDResponse

logger = logging.getLogger("uvicorn.error")
load_dotenv()


class JdService:
    def __init__(self):
        self.llm = LLMFactory.get_model("gpt-4o-mini")
        self.structured_llm = self.llm.with_structured_output(
            JDResponse,
            method="function_calling",
        )
        self.system_message = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        try:
            prompt_path = os.path.join("app", "prompts", "extract_jd_prompt2.yaml")
            if not os.path.exists(prompt_path):
                raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

            with open(prompt_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

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
            logger.error(f"Unable to load JD prompt YAML: {e}")
            return "You are an expert recruiter. Extract job description details accurately into the requested JSON format."

    async def _invoke_structured_output(self, raw_text: str) -> JDResponse:
        for attempt in range(2):
            result = await self.structured_llm.ainvoke([
                ("system", self.system_message),
                ("human", raw_text),
            ])
            if result is not None:
                return result
            logger.warning("JD extraction returned no structured output on attempt %s", attempt + 1)

        raise HTTPException(status_code=502, detail="AI did not return a JD extraction result.")

    async def extract_jd_data(self, raw_text: str) -> JDResponse:
        try:
            logger.info(f"Received JD text length: {len(raw_text)} characters")
            result = await self._invoke_structured_output(raw_text)
            pretty_output = json.dumps(result.model_dump(), indent=2, ensure_ascii=False)
            logger.info("Parsed JD data:\n" + pretty_output)
            return result

        except ValidationError as ve:
            logger.warning(f"JD validation error: {str(ve)}")
            raise HTTPException(
                status_code=422,
                detail="Extracted JD data does not match the required structure.",
            )

        except OutputParserException as ope:
            logger.warning(f"JD output parsing error: {str(ope)}")
            raise HTTPException(
                status_code=400,
                detail="AI returned an invalid JD extraction format.",
            )

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"System error in JdService: {str(e)}")
            if "401" in str(e) or "403" in str(e):
                raise HTTPException(status_code=500, detail="Invalid or unauthorized API key.")
            raise HTTPException(status_code=500, detail="JD extraction service is busy. Please try again later.")


jd_service = JdService()
