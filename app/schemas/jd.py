from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union, Any
from enum import Enum

# --- UTILS (Giữ nguyên để đồng bộ với cv.py) ---
def ensure_list(v: Any) -> List[Any]:
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

class RequirementPriority(str, Enum):
    CRITICAL = "Critical"   # Bắt buộc phải có (Knock-out criteria)
    ESSENTIAL = "Essential" # Quan trọng, cần thiết
    DESIRABLE = "Desirable" # Điểm cộng, không bắt buộc (Nice-to-have)

# --- SUB MODELS ---

class JDSkill(BaseModel):
    name: str = "Unknown"
    min_level: Union[SkillLevel, str] = SkillLevel.INTERMEDIATE
    min_years: float = Field(0.0, ge=0)
    importance: RequirementPriority = RequirementPriority.ESSENTIAL
    category: Optional[str] = "Technical"
    note: Optional[str] = None # Ghi chú cụ thể ví dụ: "Phải biết dùng Threading"

class JDExperience(BaseModel):
    min_total_years: float = Field(0.0, ge=0)
    relevant_industries: List[str] = [] # Ví dụ: Logistics, Fintech, AI
    required_positions: List[str] = [] # Ví dụ: Backend Developer, Team Lead
    description: Optional[str] = None # Mô tả các nhiệm vụ chính sẽ làm

class JDEducation(BaseModel):
    min_degree: Optional[str] = "Bachelor"
    fields_of_study: List[str] = [] # Ví dụ: IT, Computer Science
    importance: RequirementPriority = RequirementPriority.DESIRABLE

class JDProjectRequirement(BaseModel):
    domain: Optional[str] = None # Ví dụ: E-commerce, RAG System
    complexity: Optional[str] = "Medium" # Mức độ phức tạp mong muốn
    tech_stack_keywords: List[str] = [] # Các từ khóa tech mong muốn thấy trong project

# --- MAIN MODEL ---

class JDResponse(BaseModel):
    job_title: str = "Unknown"
    company_name: Optional[str] = "Unknown"
    location: Optional[str] = None
    work_mode: Optional[str] = "On-site" # Remote, Hybrid, On-site
    salary_range: Optional[str] = None

    # Yêu cầu cốt lõi
    summary: Optional[str] = None # Tóm tắt ngắn gọn JD
    experience_requirements: JDExperience = Field(default_factory=JDExperience)
    education_requirements: List[JDEducation] = []
    
    # Skill chi tiết (Dùng để match với list Skill của CV)
    skills: List[JDSkill] = []
    
    # Các yêu cầu khác
    project_requirements: List[JDProjectRequirement] = []
    languages: List[str] = [] # Ví dụ: English IELTS 6.5
    
    # Quyền lợi và ghi chú
    benefits: List[str] = []
    other_notes: Optional[str] = None 

    @field_validator('education_requirements', 'skills', 'project_requirements', 'languages', 'benefits', mode='before')
    @classmethod
    def validate_jd_lists(cls, v):
        return ensure_list(v)