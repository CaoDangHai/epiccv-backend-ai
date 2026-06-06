from typing import List, Optional, Union

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from .shared import SkillLevel, ensure_list


class SocialLinks(BaseModel):
    model_config = ConfigDict(extra="ignore")

    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other: List[str] = []

    @field_validator("other", mode="before")
    @classmethod
    def validate_other(cls, v):
        return ensure_list(v)


class Skill(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = "Unknown"
    level: Union[SkillLevel, str] = SkillLevel.BEGINNER
    years_of_experience: Optional[float] = Field(0.0, ge=0)
    category: Optional[str] = "Technical"
    remark: List[str] = []


class Language(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., validation_alias=AliasChoices("name", "language"))
    proficiency: Optional[str] = "Intermediate"


class Experience(BaseModel):
    model_config = ConfigDict(extra="ignore")

    company: Optional[str] = "Unknown"
    position: Optional[str] = "Unknown"
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = "Present"
    is_current: bool = False
    description: List[str] = []
    skills_used: List[str] = []

    @field_validator("description", "skills_used", mode="before")
    @classmethod
    def validate_lists(cls, v):
        return ensure_list(v)


class Education(BaseModel):
    model_config = ConfigDict(extra="ignore")

    school: Optional[str] = "Unknown"
    degree: Optional[str] = "Unknown"
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    graduation_year: Optional[Union[int, str]] = None
    is_current: bool = False
    gpa: Optional[Union[float, str]] = None


class Certification(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(validation_alias=AliasChoices("title", "name"))
    organization: Optional[str] = None
    year: Optional[str] = None
    name: Optional[str] = "Unknown"
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_url: Optional[str] = None


class Award(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    description: Optional[str] = None


class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = "Unknown"
    description: List[str] = []
    tech_stack: List[str] = []
    link: Optional[str] = None

    @field_validator("description", "tech_stack", mode="before")
    @classmethod
    def validate_project_fields(cls, v):
        return ensure_list(v)


class CVResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    raw_text: Optional[str] = None
    full_name: Optional[str] = "Unknown"
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = Field(None, validation_alias=AliasChoices("address", "location"))
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

    @field_validator(
        "skills",
        "work_history",
        "education",
        "projects",
        "certifications",
        "awards",
        "languages",
        "top_strengths",
        "remark",
        mode="before",
    )
    @classmethod
    def validate_main_lists(cls, v):
        return ensure_list(v)

    def to_filtered(self) -> "FilteredCVResponse":
        return FilteredCVResponse(
            summary=self.summary,
            raw_text=self.raw_text,
            total_experience_years=self.total_experience_years or 0.0,
            top_strengths=self.top_strengths,
            skills=self.skills,
            work_history=self.work_history,
            education=self.education,
            projects=self.projects,
            certifications=self.certifications,
            awards=self.awards,
            languages=self.languages,
        )


class FilteredCVResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_text: Optional[str] = None
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

    @field_validator(
        "skills",
        "work_history",
        "education",
        "projects",
        "certifications",
        "awards",
        "languages",
        "top_strengths",
        mode="before",
    )
    @classmethod
    def validate_main_lists(cls, v):
        return ensure_list(v)
