from pydantic import BaseModel, Field, field_validator
from typing import List, Any, Optional
from enum import Enum

# --- UTILS ---
def ensure_list(v: Any) -> List[Any]:
    """Hỗ trợ ép kiểu dữ liệu về list, xử lý linh hoạt đầu ra của LLM"""
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        return [s.strip() for s in v.split('\n') if s.strip()]
    return [v]

# --- SHARED ENUMS ---
class SkillLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"
    UNKNOWN = "Unknown"

class RequirementPriority(str, Enum):
    CRITICAL = "Critical"
    ESSENTIAL = "Essential"
    DESIRABLE = "Desirable"

class MatchStatus(str, Enum):
    FULL_MATCH = "Full Match"
    PARTIAL_MATCH = "Partial Match"
    MISSING = "Missing"
    EXCEEDS = "Exceeds"

# --- SHARED SUB MODELS ---
class OverallAssessment(BaseModel):
    match_percentage: float = Field(..., ge=0, le=100)
    summary: str = Field(..., description="Professional verdict or summary")
    strengths: List[str] = []
    weaknesses: List[str] = []
    improvement_notes: List[str] = []

    @field_validator('strengths', 'weaknesses', 'improvement_notes', mode='before')
    @classmethod
    def validate_lists(cls, v):
        return ensure_list(v)