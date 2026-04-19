from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union, Any
from enum import Enum

# --- UTILS ---
def ensure_list(v: Any) -> List[Any]:
    """Hàm hỗ trợ ép kiểu dữ liệu về list để tránh lỗi AI trả về string đơn lẻ hoặc null"""
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        # Trường hợp AI trả về các dòng xuống hàng thay vì list
        return [s.strip() for s in v.split('\n') if s.strip()]
    return [v]

# --- ENUM ---
class SkillLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"
    UNKNOWN = "Unknown"

# --- SUB MODELS ---

class Skill(BaseModel):
    name: Optional[str] = "Unknown"
    level: Union[SkillLevel, str] = SkillLevel.INTERMEDIATE 
    years_of_experience: Optional[float] = Field(0.0, ge=0)
    category: Optional[str] = "Technical"

class Experience(BaseModel):
    company: Optional[str] = "Unknown"
    position: Optional[str] = "Unknown"
    location: Optional[str] = None
    start_date: Optional[str] = None 
    end_date: Optional[str] = "Present"
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
    graduation_year: Optional[Union[int, str]] = None 
    gpa: Optional[Union[float, str]] = None

class Certification(BaseModel):
    name: Optional[str] = "Unknown"
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_url: Optional[str] = None # Dùng str để tránh lỗi format URL từ AI

class Project(BaseModel):
    name: Optional[str] = "Unknown"
    description: Optional[str] = None
    tech_stack: List[str] = []
    link: Optional[str] = None # Dùng str để tránh lỗi format URL từ AI

    @field_validator('tech_stack', mode='before')
    @classmethod
    def validate_tech_stack(cls, v):
        return ensure_list(v)

# --- MAIN MODEL ---

class CVResponse(BaseModel):
    full_name: Optional[str] = "Unknown"
    email: Optional[str] = None # Dùng str để AI dễ thở hơn EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    age: Optional[Union[int, str]] = None 

    links: List[str] = []
    summary: Optional[str] = None
    total_experience_years: Optional[float] = Field(default=0.0, ge=0)

    skills: List[Skill] = []
    work_history: List[Experience] = []
    education: List[Education] = []
    projects: List[Project] = []
    certifications: List[Certification] = []
    languages: List[str] = []
    top_strengths: List[str] = []

    @field_validator('links', 'skills', 'work_history', 'education', 'projects', 'certifications', 'languages', 'top_strengths', mode='before')
    @classmethod
    def validate_main_lists(cls, v):
        return ensure_list(v)