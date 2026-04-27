from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
from .shared import ensure_list, SkillLevel, RequirementPriority, MatchStatus, OverallAssessment

class SkillMatch(BaseModel):
    name: str
    category: str = "Technical"
    level_cv: SkillLevel = Field(..., alias="cv_level")
    level_jd_req: SkillLevel = Field(..., alias="jd_level")
    years_of_experience: float = Field(0.0, ge=0)
    match_status: MatchStatus
    priority: RequirementPriority
    weight: float = 1.0
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
    culture_score: float = Field(..., ge=0, le=100)
    vibe_check: str = Field(..., description="How well candidate matches culture_fit & keywords")
    industry_relevance: bool = Field(..., description="Does work_history match relevant_industries?")

class ComparisonAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_qualified: bool 
    match_percentage: float = Field(..., alias="score")
    overall: OverallAssessment
    experience_alignment: str = Field(..., description="Alignment with required_positions and responsibilities")
    total_years_gap: float = Field(..., description="Difference between CV total_years and JD min_total_years")
    culture_fit: CultureAndIndustryFit
    matched_skills: List[SkillMatch] = []
    missing_skills: List[SkillGap] = []

    @field_validator('matched_skills', 'missing_skills', mode='before')
    @classmethod
    def validate_main_lists(cls, v):
        return ensure_list(v)