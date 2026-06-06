import logging

from langchain_openai import ChatOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for cached LLM instances served through the YesScale proxy."""

    _instances = {}

    YES_SCALE_MODELS = {
        "gpt-4o": {"temp": 0.2},
        "gpt-4.1-mini": {"temp": 0},
        "gpt-4o-mini": {"temp": 0},
        "gpt-5-mini": {"temp": 0},
        "gpt-5": {"temp": 0},
        "gemini-3-flash": {"temp": 0.1},
        "gemini-3-pro": {"temp": 0.2},
        "gemini-3-flash-preview": {"temp": 0},
    }

    @classmethod
    def get_model(cls, model_name: str, temperature: float = None):
        temp_to_use = (
            temperature
            if temperature is not None
            else cls.YES_SCALE_MODELS.get(model_name, {}).get("temp", 0.2)
        )
        instance_key = f"{model_name}_{temp_to_use}"

        if instance_key in cls._instances:
            return cls._instances[instance_key]

        if model_name not in cls.YES_SCALE_MODELS:
            logger.warning(f"Model {model_name} is not listed in YES_SCALE_MODELS.")

        try:
            instance = ChatOpenAI(
                model=model_name,
                api_key=settings.YES_SCALE_API_KEY,
                base_url=settings.YES_SCALE_BASE_URL,
                temperature=temp_to_use,
                max_retries=3,
                timeout=60,
            )

            cls._instances[instance_key] = instance
            return instance

        except Exception as e:
            logger.error(f"Failed to initialize LLM {model_name}: {str(e)}")
            raise RuntimeError(f"Unable to connect to YesScale for model {model_name}.")

    @classmethod
    def clear_cache(cls):
        cls._instances.clear()
