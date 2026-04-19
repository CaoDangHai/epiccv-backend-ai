from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

class LLMFactory:
    _instances = {}

    @classmethod
    def get_model(cls, model_name: str):
        # (Singleton)
        if model_name in cls._instances:
            return cls._instances[model_name]

        # Nếu chưa có, tiến hành khởi tạo 
        
        if model_name == "gemini-2.5-flash":
            instance = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=settings.GEMINI_KEY)
        elif model_name == "gemini-2.5-pro":
            instance = ChatGoogleGenerativeAI(model="gemini-2.5-pro", api_key=settings.GEMINI_KEY)
        else:
            raise ValueError(f"Model {model_name} không được hỗ trợ.")

        cls._instances[model_name] = instance
        return instance