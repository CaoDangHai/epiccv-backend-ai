from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union, Any
from enum import Enum

# --- UTILS ---
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
    CRITICAL = "Critical"   # Bắt buộc (Must-have)
    ESSENTIAL = "Essential" # Quan trọng (Should-have)
    DESIRABLE = "Desirable" # Điểm cộng (Nice-to-have)

class JobType(str, Enum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    INTERN = "Intern"
    FREELANCE = "Freelance"

# --- SUB MODELS ---

class SalaryRange(BaseModel):
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    currency: str = "VND"
    is_negotiable: bool = True

class JDSkill(BaseModel):
    name: str = "Unknown"
    min_level: Union[SkillLevel, str] = SkillLevel.INTERMEDIATE
    min_years: float = Field(0.0, ge=0)
    importance: RequirementPriority = RequirementPriority.ESSENTIAL
    category: str = "Technical" # Để map với category bên CV

class JDLanguage(BaseModel):
    name: str
    min_proficiency: Optional[str] = "Professional" # e.g., IELTS 6.5, JLPT N2
    importance: RequirementPriority = RequirementPriority.DESIRABLE

class JDExperience(BaseModel):
    min_total_years: float = Field(0.0, ge=0)
    relevant_industries: List[str] = []
    required_positions: List[str] = []
    key_responsibilities: List[str] = [] # Tách riêng trách nhiệm để dễ so sánh năng lực

    @field_validator('relevant_industries', 'required_positions', 'key_responsibilities', mode='before')
    @classmethod
    def validate_exp_lists(cls, v):
        return ensure_list(v)

class JDEducation(BaseModel):
    min_degree: Optional[str] = "Bachelor"
    fields_of_study: List[str] = []
    importance: RequirementPriority = RequirementPriority.DESIRABLE

class JDProjectRequirement(BaseModel):
    domain: Optional[str] = None # e.g., Fintech, E-commerce
    tech_stack_keywords: List[str] = [] 
    description: Optional[str] = None # Kỳ vọng cụ thể về project ứng viên từng làm

# --- MAIN MODEL ---

class JDResponse(BaseModel):
    job_title: str = "Unknown"
    company_name: Optional[str] = "Unknown"
    job_type: JobType = JobType.FULL_TIME
    location: Optional[str] = None
    work_mode: str = "On-site" # Remote, Hybrid, On-site
    
    # Cấu trúc hóa lương thay vì để String
    salary: Optional[SalaryRange] = Field(default_factory=SalaryRange)
    
    summary: Optional[str] = None
    
    # Yêu cầu chi tiết
    experience_requirements: JDExperience = Field(default_factory=JDExperience)
    education_requirements: List[JDEducation] = []
    skills: List[JDSkill] = []
    languages: List[JDLanguage] = [] # Đồng bộ cấu trúc với CV
    
    # Project & Văn hóa
    project_requirements: List[JDProjectRequirement] = []
    benefits: List[str] = []
    culture_fit: List[str] = [] # Các yêu cầu về tính cách, thái độ (Soft skills đặc thù)
    
    # Metadata phục vụ hệ thống
    keywords: List[str] = [] # Các tags quan trọng để index vào Vector DB (PostgreSQL pgvector)
    other_notes: Optional[str] = None 

    @field_validator(
        'education_requirements', 'skills', 'languages', 
        'project_requirements', 'benefits', 'culture_fit', 'keywords', 
        mode='before'
    )
    @classmethod
    def validate_jd_lists(cls, v):
        return ensure_list(v)

class FilteredJDResponse(BaseModel):
    """Bản FILTERED - Chỉ chứa các mốc so sánh trình độ (Benchmark)"""
    job_title: str = "Unknown"
    summary: Optional[str] = None
    
    # Giữ lại toàn bộ logic yêu cầu chuyên môn
    experience_requirements: JDExperience = Field(default_factory=JDExperience)
    education_requirements: List[JDEducation] = []
    skills: List[JDSkill] = []
    languages: List[JDLanguage] = []
    project_requirements: List[JDProjectRequirement] = []
    
    # Giữ lại văn hóa và từ khóa (Quan trọng để match "vibe" và search)
    culture_fit: List[str] = []
    keywords: List[str] = []

    @field_validator(
        'education_requirements', 'skills', 'languages', 
        'project_requirements', 'culture_fit', 'keywords', 
        mode='before'
    )
    @classmethod
    def validate_filtered_lists(cls, v):
        return ensure_list(v)

    @classmethod
    def from_full_jd(cls, full_jd: JDResponse) -> "FilteredJDResponse":
        """Factory method: Lọc bỏ 'rác' hành chính, giữ lại 'xương sống' nghiệp vụ"""
        full_data = full_jd.model_dump()
        
        # Những key quyết định trình độ và độ phù hợp
        target_keys = {
            "job_title", "summary", "experience_requirements", 
            "education_requirements", "skills", "languages", 
            "project_requirements", "culture_fit", "keywords"
        }
        
        filtered_data = {k: v for k, v in full_data.items() if k in target_keys}
        return cls(**filtered_data)