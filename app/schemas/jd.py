from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
from .shared import ensure_list, SkillLevel, RequirementPriority, MatchStatus, OverallAssessment

class SkillMatch(BaseModel):
    name: str
    category: str = "Technical"
    level: SkillLevel = SkillLevel.BEGINNER
    years_of_experience: float = Field(0.0, ge=0)
    match_status: MatchStatus = MatchStatus.FULL_MATCH
    cv_evidence: str = Field(..., description="Short keywords/project name from CV")
    score: float = Field(..., ge=0, le=1)
    remark: Optional[str] = None

class SkillGap(BaseModel):
    name: str
    importance: RequirementPriority = RequirementPriority.ESSENTIAL
    gap_description: str = Field(..., description="Short gap reason")
    recommendation: str = Field(..., description="Actionable tip for roadmap")

class SkillGroupAssessment(BaseModel):
    group_name: str
    score: float = Field(..., ge=0, le=100)
    assessment: str = Field(..., description="Concise group summary (max 15 words)")

class JDResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_qualified: bool 
    match_percentage: float = Field(..., alias="score")
    overall: OverallAssessment
    skill_groups: List[SkillGroupAssessment] = []
    matched_skills: List[SkillMatch] = []
    missing_skills: List[SkillGap] = []
    experience_fit_summary: str = Field(..., description="Brief exp alignment check")

    @field_validator('skill_groups', 'matched_skills', 'missing_skills', mode='before')
    @classmethod
    def validate_main_lists(cls, v):
        return ensure_list(v)