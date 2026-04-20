from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Any
from enum import Enum

# --- UTILS ---
def ensure_list(v: Any) -> List[Any]:
    if v is None: return []
    if isinstance(v, list): return v
    if isinstance(v, str): return [s.strip() for s in v.split('\n') if s.strip()]
    return [v]

# --- ENUMS ---
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
    level_cv: SkillLevel = Field(..., alias="cv_level")
    level_jd_req: SkillLevel = Field(..., alias="jd_level")
    years_of_experience: float = Field(0.0, ge=0)
    match_status: MatchStatus
    priority: RequirementPriority
    weight: float = 1.0
    
    # Bằng chứng trích xuất từ Projects hoặc Work History trong FilteredCV
    cv_evidence: str = Field(..., description="Evidence from Projects/Experience descriptions")
    score: float = Field(..., ge=0, le=1)
    remark: Optional[str] = None

class SkillGap(BaseModel):
    name: str
    importance: RequirementPriority
    weight: float = 1.0
    gap_description: str
    recommendation: str = Field(..., description="Actionable learning path for this gap")

class CultureAndIndustryFit(BaseModel):
    """Phân tích dựa trên Culture Fit và Keywords từ FilteredJD"""
    culture_score: float = Field(..., ge=0, le=100)
    vibe_check: str = Field(..., description="How well candidate matches culture_fit & keywords")
    industry_relevance: bool = Field(..., description="Does work_history match relevant_industries?")

class OverallAssessment(BaseModel):
    match_percentage: float = Field(..., ge=0, le=100)
    summary: str = Field(..., description="Concise professional verdict")
    strengths: List[str] = []
    weaknesses: List[str] = []
    improvement_notes: List[str] = []

    @field_validator('strengths', 'weaknesses', 'improvement_notes', mode='before')
    @classmethod
    def validate_lists(cls, v):
        return ensure_list(v)

# --- MAIN MODEL ---

class ComparisonAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_qualified: bool 
    match_percentage: float = Field(..., alias="score")
    
    overall: OverallAssessment
    
    # Đối chiếu sâu về kinh nghiệm (Sử dụng dữ liệu từ JDExperience)
    experience_alignment: str = Field(..., description="Alignment with required_positions and responsibilities")
    total_years_gap: float = Field(..., description="Difference between CV total_years and JD min_total_years")

    # Phân tích văn hóa & ngành nghề
    culture_fit: CultureAndIndustryFit

    # Danh sách chi tiết
    matched_skills: List[SkillMatch] = []
    missing_skills: List[SkillGap] = []

    @field_validator('matched_skills', 'missing_skills', mode='before')
    @classmethod
    def validate_main_lists(cls, v):
        return ensure_list(v)