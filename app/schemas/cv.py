from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import List, Optional, Union, Any
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

# --- ENUM ---
class SkillLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"
    UNKNOWN = "Unknown"

# --- SUB MODELS ---

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
    # Mặc định Beginner theo yêu cầu logic của hệ thống nếu thiếu dữ liệu
    level: Union[SkillLevel, str] = SkillLevel.BEGINNER 
    years_of_experience: Optional[float] = Field(0.0, ge=0)
    category: Optional[str] = "Technical" # e.g., Framework, Language, Soft Skill, Tool

class Language(BaseModel):
    name: str
    proficiency: Optional[str] = "Intermediate" # e.g., Native, Professional, IELTS 7.5

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
    description: Optional[str] = None
    tech_stack: List[str] = []
    link: Optional[str] = None

    @field_validator('tech_stack', mode='before')
    @classmethod
    def validate_tech_stack(cls, v):
        return ensure_list(v)

# --- MAIN MODEL ---

class CVResponse(BaseModel):
    full_name: Optional[str] = "Unknown"
    email: Optional[str] = None 
    phone: Optional[str] = None
    address: Optional[str] = None
    age: Optional[Union[int, str]] = None 
    
    # Bóc tách để dễ dàng thực hiện profile enrichment
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

    @field_validator(
        'skills', 'work_history', 'education', 'projects', 
        'certifications', 'awards', 'languages', 'top_strengths', 
        mode='before'
    )
    @classmethod
    def validate_main_lists(cls, v):
        return ensure_list(v)
    


# Filterd CV
# Filterd CV
class FilteredCVResponse(BaseModel):
    """Bản CV đã lược bỏ PII (Personal Identifying Information)"""
    
    # Giữ lại tóm tắt chuyên môn
    summary: Optional[str] = None
    total_experience_years: float = 0.0
    top_strengths: List[str] = []

    # Giữ trọn vẹn các danh sách năng lực (Nested Models)
    skills: List[Skill] = []
    work_history: List[Experience] = []
    education: List[Education] = []
    projects: List[Project] = []
    certifications: List[Certification] = []
    awards: List[Award] = []
    languages: List[Language] = []

    @field_validator(
        'skills', 'work_history', 'education', 'projects', 
        'certifications', 'awards', 'languages', 'top_strengths', 
        mode='before'
    )
    @classmethod
    def validate_main_lists(cls, v):
        return ensure_list(v)
    
    @classmethod
    def from_full_cv(cls, full_cv: CVResponse) -> "FilteredCVResponse":
        """
        Factory method: Chuyển đổi từ CVResponse sang FilteredCVResponse.
        Chỉ giữ lại các trường liên quan đến trình độ chuyên môn.
        """
        # Convert full_cv sang dict (Pydantic v2 dùng model_dump)
        full_data = full_cv.model_dump()

        # Định nghĩa các key 'nghiệp vụ' cần giữ lại
        qualified_keys = {
            "summary", 
            "total_experience_years", 
            "top_strengths", 
            "skills", 
            "work_history", 
            "education", 
            "projects", 
            "certifications", 
            "awards", 
            "languages"
        }

        # Lọc dữ liệu: chỉ lấy những gì nằm trong qualified_keys
        filtered_data = {k: v for k, v in full_data.items() if k in qualified_keys}

        # Khởi tạo instance mới của FilteredCVResponse
        return cls(**filtered_data)