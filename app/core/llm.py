from langchain_openai import ChatOpenAI
from app.core.config import settings
import logging

# Thiết lập log để dễ theo dõi khi gọi model
logger = logging.getLogger(__name__)

class LLMFactory:
    """
    Factory quản lý các instance LLM thông qua YesScale Proxy.
    """
    _instances = {}

    # Danh sách các model phổ biến trên YesScale và cấu hình temperature mặc định
    # Bạn có thể thêm/bớt model tùy theo gói đăng ký tại YesScale
    YES_SCALE_MODELS = {
        # OpenAI Models
        "gpt-4o": {"temp": 0.2},
        "gpt-4.1-mini" : {"temp": 0},
        "gpt-4o-mini": {"temp": 0},
        "gpt-5-mini": {"temp": 0},
        "gpt-5" : {"temp": 0},
        
        
        # Google Gemini (Chạy qua proxy OpenAI của YesScale)
        "gemini-3-flash": {"temp": 0.1},
        "gemini-3-pro": {"temp": 0.2},
        "gemini-3-flash-preview" : {"temp": 0},
        
        
        
    }

    @classmethod
    def get_model(cls, model_name: str, temperature: float = None):
        """
        Lấy instance của model. 
        :param model_name: Tên định danh của model (vd: 'gpt-4o')
        :param temperature: Ghi đè temp mặc định nếu cần
        """
        
        # Tạo cache key dựa trên model và temp để tránh conflict khi dùng cùng model nhưng khác temp
        temp_to_use = temperature if temperature is not None else cls.YES_SCALE_MODELS.get(model_name, {}).get("temp", 0.2)
        instance_key = f"{model_name}_{temp_to_use}"

        if instance_key in cls._instances:
            return cls._instances[instance_key]

        # Kiểm tra xem model có trong danh sách hỗ trợ không (Gợi ý nếu gõ sai)
        if model_name not in cls.YES_SCALE_MODELS:
            logger.warning(f"Model {model_name} không nằm trong danh sách YES_SCALE_MODELS.")

        try:
            # Khởi tạo instance qua YesScale (Dùng chuẩn ChatOpenAI)
            instance = ChatOpenAI(
                model=model_name,
                api_key=settings.YES_SCALE_API_KEY,  
                base_url=settings.YES_SCALE_BASE_URL, 
                temperature=temp_to_use,
                max_retries=3,
                timeout=60, # Tăng timeout vì một số model như Claude/Gemini Pro phản hồi khá lâu
          
            )

            # Lưu vào bộ nhớ đệm
            cls._instances[instance_key] = instance
            return instance

        except Exception as e:
            logger.error(f"Lỗi khi khởi tạo LLM {model_name}: {str(e)}")
            raise RuntimeError(f"Không thể kết nối với YesScale cho model {model_name}.")

    @classmethod
    def clear_cache(cls):
        """Xóa toàn bộ instance đã lưu (Dùng khi cần refresh config)"""
        cls._instances.clear()