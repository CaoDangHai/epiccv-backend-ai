from pydantic import AliasChoices, BaseModel, Field, field_validator
from typing import List, Optional, Union, Any
from .shared import ensure_list, SkillLevel

class SocialLinks(BaseModel):
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other: List[str] = []

    @field_validator('other', mode='before')
    @classmethod
    def validate_other(cls, v):
        return ensure_list(v)

class Skill(BaseModel):
    name: Optional[str] = "Unknown"
    level: Union[SkillLevel, str] = SkillLevel.BEGINNER 
    years_of_experience: Optional[float] = Field(0.0, ge=0)
    category: Optional[str] = "Technical"

class Language(BaseModel):
    name: str = Field(..., validation_alias=AliasChoices('name', 'language'))
    proficiency: Optional[str] = "Intermediate"

class Experience(BaseModel):
    company: Optional[str] = "Unknown"
    position: Optional[str] = "Unknown"
    location: Optional[str] = None
    start_date: Optional[str] = None 
    end_date: Optional[str] = "Present"
    is_current: bool = False
    description: List[str] = []
    skills_used: List[str] = []

    @field_validator('description', 'skills_used', mode='before')
    @classmethod
    def validate_lists(cls, v):
        return ensure_list(v)

class Education(BaseModel):
    school: Optional[str] = "Unknown"
    degree: Optional[str] = "Unknown"
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    graduation_year: Optional[Union[int, str]] = None 
    is_current: bool = False
    gpa: Optional[Union[float, str]] = None

class Certification(BaseModel):
    name: Optional[str] = "Unknown"
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_url: Optional[str] = None

class Award(BaseModel):
    title: str
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    description: Optional[str] = None

class Project(BaseModel):
    name: Optional[str] = "Unknown"
    description: List[str] = [] 
    tech_stack: List[str] = []
    link: Optional[str] = None

    @field_validator('description', 'tech_stack', mode='before')
    @classmethod
    def validate_project_fields(cls, v):
        return ensure_list(v)

class CVResponse(BaseModel):
    full_name: Optional[str] = "Unknown"
    email: Optional[str] = None 
    phone: Optional[str] = None
    address: Optional[str] = None
    age: Optional[Union[int, str]] = None 
    social_links: Optional[SocialLinks] = Field(default_factory=SocialLinks)
    summary: Optional[str] = None
    total_experience_years: Optional[float] = Field(default=0.0, ge=0)
    skills: List[Skill] = []
    work_history: List[Experience] = []
    education: List[Education] = []
    projects: List[Project] = []
    certifications: List[Certification] = []
    awards: List[Award] = []
    languages: List[Language] = []
    top_strengths: List[str] = []
    remark: List[str] = [] 

    @field_validator('skills', 'work_history', 'education', 'projects', 'certifications', 'awards', 'languages', 'top_strengths', 'remark', mode='before')
    @classmethod
    def validate_main_lists(cls, v):
        return ensure_list(v)

class FilteredCVResponse(BaseModel):
    summary: Optional[str] = None
    total_experience_years: float = 0.0
    top_strengths: List[str] = []
    skills: List[Skill] = []
    work_history: List[Experience] = []
    education: List[Education] = []
    projects: List[Project] = []
    certifications: List[Certification] = []
    awards: List[Award] = []
    languages: List[Language] = []

    @field_validator('skills', 'work_history', 'education', 'projects', 'certifications', 'awards', 'languages', 'top_strengths', mode='before')
    @classmethod
    def validate_main_lists(cls, v):
        return ensure_list(v)
    
    @classmethod
    def from_full_cv(cls, full_cv: CVResponse) -> "FilteredCVResponse":
        full_data = full_cv.model_dump()
        qualified_keys = {"summary", "total_experience_years", "top_strengths", "skills", "work_history", "education", "projects", "certifications", "awards", "languages"}
        filtered_data = {k: v for k, v in full_data.items() if k in qualified_keys}
        return cls(**filtered_data)