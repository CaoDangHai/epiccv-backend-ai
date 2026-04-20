from pydantic import BaseModel, Field, field_validator, HttpUrl, ConfigDict
from typing import List, Optional, Any, Union
from enum import Enum

# --- REUSE FROM result.py / cv.py ---
class SkillLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"
    UNKNOWN = "Unknown"

# --- UTILS (Giữ nguyên của bạn) ---
def ensure_list(v: Any) -> List[Any]:
    if v is None: return []
    if isinstance(v, list): return v
    if isinstance(v, str): return [s.strip() for s in v.split('\n') if s.strip()]
    return [v]

# --- SUB MODELS ---

class LearningResource(BaseModel):
    title: str
    url: Union[HttpUrl, str] # Linh hoạt hơn cho LLM
    resource_type: str = "Documentation" # e.g., Video, Repo, Article
    duration: Optional[str] = None 
    description: Optional[str] = None

class LearningOutcome(BaseModel):
    skill_name: str
    target_level: SkillLevel = SkillLevel.INTERMEDIATE # Đồng bộ Enum
    achieved_competencies: List[str] = []

    @field_validator('achieved_competencies', mode='before')
    @classmethod
    def validate_list(cls, v):
        return ensure_list(v)

class RoadmapStep(BaseModel):
    order: int = Field(..., ge=1)
    title: str
    description: str
    # Liên kết trực tiếp với missing_skills từ result.py
    linked_skill_gaps: List[str] = [] 
    focus_skills: List[str] = []
    estimated_duration: str 
    
    key_topics: List[str] = []
    resources: List[LearningResource] = []
    
    # Thêm màu sắc/icon 
    ui_color: str = "primary" # blue, green, orange, v.v.
    is_completed: bool = False

    @field_validator('linked_skill_gaps', 'focus_skills', 'key_topics', 'resources', mode='before')
    @classmethod
    def validate_lists(cls, v):
        return ensure_list(v)

# --- MAIN MODEL ---

class LearningRoadmapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True) # Đồng bộ với result.py

    roadmap_id: Optional[str] = None
    target_job_title: str
    summary: str = Field(..., description="Overview of the learning journey")
    
    difficulty: str = "Intermediate"
    estimated_total_time: str 
    
    steps: List[RoadmapStep] = []
    final_outcomes: List[LearningOutcome] = []
    
    mentor_advice: Optional[str] = None

    @field_validator('steps', 'final_outcomes', mode='before')
    @classmethod
    def validate_main_lists(cls, v):
        return ensure_list(v)