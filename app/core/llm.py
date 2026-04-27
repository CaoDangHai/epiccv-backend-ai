from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from app.core.config import settings

class LLMFactory:
    _instances = {}

    # Cấu hình danh sách các model dùng qua cổng Proxy (trollllm)
    PROXY_MODELS = {
        "claude-haiku-4.5": {"temp": 0},
        "gemini-3.1-pro-preview": {"temp": 0},
        "gpt-5.2": {"temp": 0.1},
        "gpt-4o-mini": {"temp": 0},
    }

    # Cấu hình danh sách các model dùng trực tiếp Google AI Studio
    GOOGLE_MODELS = {
        "gemini-2.5-flash-lite" : {"temp": 0}, # dung dc
        "gemini-2.5-flash": {"temp": 0}, # dung dc 
        "gemini-3-flash": {"temp": 0},
        "gemini-3.1-pro": {"temp": 0.3},
        "gemini-3.1-pro-preview": {"temp": 0},
        "gemini-3.1-flash-lite-preview": {"temp": 0}, # dung dc
    }

    @classmethod
    def get_model(cls, model_name: str):
        # 1. Kiểm tra Singleton
        if model_name in cls._instances:
            return cls._instances[model_name]

        instance = None

        # 2. Khởi tạo cho các model qua cổng OpenAI Compatible (trollllm)
        if model_name in cls.PROXY_MODELS:
            config = cls.PROXY_MODELS[model_name]
            instance = ChatOpenAI(
                model=model_name,
                api_key=settings.TROLLLM_KEY,
                openai_api_base="https://chat.trollllm.xyz/v1",
                temperature=config.get("temp", 0),
                max_retries=2,
                
            )

        # 3. Khởi tạo cho các model Google chính chủ
        elif model_name in cls.GOOGLE_MODELS:
            instance = ChatGoogleGenerativeAI(
                model=model_name,
                api_key=settings.GOOGLE_KEY,
                temperature=0 # Thường để 0 cho các tác vụ trích xuất CV
                
            )

        else:
            raise ValueError(f"Model {model_name} chưa được cấu hình trong Factory.")

        # Lưu vào bộ nhớ instance và trả về
        cls._instances[model_name] = instance
        return instance