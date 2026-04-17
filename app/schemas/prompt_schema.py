from pydantic import BaseModel
from typing import Optional

class PromptEvaluationCriteria(BaseModel):
    format_integrity: bool  # LLM có trả về đúng JSON không?
    skill_accuracy: float   # Điểm chính xác kỹ năng (1-10)
    no_hallucination: bool  # Có bịa kỹ năng không?
    reasoning_quality: int  # Độ sâu của lời giải thích (1-5)
    token_usage: Optional[int] # Chi phí (số token)