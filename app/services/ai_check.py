import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Cấu hình API Key từ file .env
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def call_llm(prompt_content: str):
    """
    Hàm gọi API để thực hiện Task 55
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Ép model trả về JSON nếu ông dùng kỹ thuật Structured Output
        response = model.generate_content(
            prompt_content,
            generation_config={"response_mime_type": "application/json"}
        )
        return response.text
    except Exception as e:
        return f"Lỗi gọi API: {str(e)}"