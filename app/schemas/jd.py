from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Any
from enum import Enum

# --- UTILS ---
def ensure_list(v: Any) -> List[Any]:
    if v is None: return []
    if isinstance(v, list): return v
    if isinstance(v, str): return [s.strip() for s in v.split('\n') if s.strip()]
    return [v]

# --- ENUMS (Đồng bộ hoàn toàn với JD Schema của bạn) ---
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

# --- SUB MODELS ---

class SkillMatch(BaseModel):
    name: str
    category: str = "Technical"
    level: SkillLevel = SkillLevel.BEGINNER # Mặc định Beginner như bạn muốn
    years_of_experience: float = Field(0.0, ge=0)
    match_status: MatchStatus = MatchStatus.FULL_MATCH
    # Giới hạn AI trích dẫn ngắn để tiết kiệm token
    cv_evidence: str = Field(..., description="Short keywords/project name from CV")
    score: float = Field(..., ge=0, le=1)
    remark: Optional[str] = Field(None, description="Note if level/exp mismatch")

class SkillGap(BaseModel):
    name: str
    importance: RequirementPriority = RequirementPriority.ESSENTIAL
    gap_description: str = Field(..., description="Short gap reason")
    recommendation: str = Field(..., description="Actionable tip for roadmap")

class SkillGroupAssessment(BaseModel):
    group_name: str # e.g., Backend, Frontend, Soft Skills
    score: float = Field(..., ge=0, le=100)
    assessment: str = Field(..., description="Concise group summary (max 15 words)")

class OverallAssessment(BaseModel):
    match_percentage: float = Field(..., ge=0, le=100)
    summary: str = Field(..., description="One-sentence verdict")
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    improvement_notes: List[str] = Field(default_factory=list)

    # Quan trọng: Validator cho các list bên trong sub-model
    @field_validator('strengths', 'weaknesses', 'improvement_notes', mode='before')
    @classmethod
    def validate_lists(cls, v):
        return ensure_list(v)

# --- MAIN MODEL ---

class ComparisonAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Đưa các trường quan trọng lên đầu để Parser xử lý trước
    is_qualified: bool 
    match_percentage: float = Field(..., alias="score") # Alias để linh hoạt mapping
    
    overall: OverallAssessment
    skill_groups: List[SkillGroupAssessment] = []
    
    matched_skills: List[SkillMatch] = []
    missing_skills: List[SkillGap] = []
    
    experience_fit_summary: str = Field(..., description="Brief exp alignment check")

    @field_validator('skill_groups', 'matched_skills', 'missing_skills', mode='before')
    @classmethod
    def validate_main_lists(cls, v):
        return ensure_list(v)