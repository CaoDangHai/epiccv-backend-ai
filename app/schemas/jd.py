from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .shared import RequirementPriority, SkillLevel, ensure_list


class JDSalary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    min_val: Optional[float] = None
    max_val: Optional[float] = None
    currency: str = "VND"
    is_negotiable: bool = True


class JDSkillRequirement(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    category: str = "Technical"
    min_level: SkillLevel = SkillLevel.BEGINNER
    priority: RequirementPriority = RequirementPriority.ESSENTIAL
    min_years: float = Field(0.0, ge=0)
    is_mandatory: bool = True
    weight: float = Field(1.0, ge=0, le=2.0)


class JDContext(BaseModel):
    role_mission: str = Field(..., description="Primary mission of this role")
    ideal_persona: str = Field(..., description="Profile of the ideal candidate")
    working_culture: List[str] = []
    team_structure: Optional[str] = None
    growth_opportunities: List[str] = []


class JDResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    raw_text: Optional[str] = None
    job_title: str = "Unknown Position"
    company_name: str = "Unknown"
    job_location: Optional[str] = None
    employment_type: str = "Full-time"
    salary_info: JDSalary = Field(default_factory=JDSalary)
    required_skills: List[JDSkillRequirement] = []
    soft_skills: List[JDSkillRequirement] = []
    min_total_experience_years: float = 0.0
    preferred_seniority: str = "Middle"
    education_requirements: List[str] = []
    job_context: JDContext
    responsibilities: List[str] = []
    requirements_summary: List[str] = []
    benefits: List[str] = []
    industry_tags: List[str] = []
    tool_stack: List[str] = []

    @field_validator(
        "required_skills",
        "soft_skills",
        "education_requirements",
        "responsibilities",
        "requirements_summary",
        "benefits",
        "industry_tags",
        "tool_stack",
        mode="before",
    )
    @classmethod
    def validate_main_lists(cls, v):
        return ensure_list(v)
