from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Union
from .shared import ensure_list, SkillLevel, RequirementPriority 

class JDSalary(BaseModel):
    model_config = ConfigDict(extra='ignore')
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    currency: str = "VND"
    is_negotiable: bool = True

class JDSkillRequirement(BaseModel):
    """Chi tiết về từng kỹ năng yêu cầu để sau này so sánh với CV"""
    model_config = ConfigDict(extra='ignore')
    name: str
    category: str = "Technical" 
    min_level: SkillLevel = SkillLevel.BEGINNER 
    priority: RequirementPriority = RequirementPriority.ESSENTIAL 
    min_years: float = Field(0.0, ge=0)
    is_mandatory: bool = True 
    weight: float = Field(1.0, ge=0, le=2.0) # Trọng số quan trọng để tính điểm sau này

class JDContext(BaseModel):
    """Phác họa bối cảnh công việc - Đây là phần nâng cấp 'dài' ra"""
    role_mission: str = Field(..., description="Sứ mệnh chính của vị trí này")
    ideal_persona: str = Field(..., description="Mô tả chân dung ứng viên lý tưởng")
    working_culture: List[str] = []
    team_structure: Optional[str] = None
    growth_opportunities: List[str] = []

class JDResponse(BaseModel):
    """Schema trích xuất JD toàn diện, không lẫn lộn với kết quả so sánh"""
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    # 1. Thông tin định danh
    job_title: str
    company_name: str = "Unknown"
    job_location: Optional[str] = None
    employment_type: str = "Full-time" # Remote, Hybrid...

    # 2. Yêu cầu chuyên môn 
    salary_info: JDSalary = Field(default_factory=JDSalary)
    required_skills: List[JDSkillRequirement] = []
    soft_skills: List[JDSkillRequirement] = []
    
    # 3. Kinh nghiệm & Học vấn
    min_total_experience_years: float = 0.0
    preferred_seniority: str = "Middle"
    education_requirements: List[str] = []

    # 4. Bối cảnh & Mô tả 
    job_context: JDContext
    responsibilities: List[str] = []
    requirements_summary: List[str] = []
    benefits: List[str] = []
    
    # 5. Metadata để hệ thống lọc
    industry_tags: List[str] = []
    tool_stack: List[str] = []

    @field_validator('required_skills', 'soft_skills', 'education_requirements', 
                     'responsibilities', 'requirements_summary', 'benefits', 
                     'industry_tags', 'tool_stack', mode='before')
    @classmethod
    def validate_main_lists(cls, v):
        return ensure_list(v) 