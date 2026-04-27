from pydantic import BaseModel, Field, field_validator, HttpUrl, ConfigDict
from typing import List, Optional, Union
from .shared import ensure_list, SkillLevel

class LearningResource(BaseModel):
    title: str
    url: Union[HttpUrl, str]
    resource_type: str = "Documentation"
    duration: Optional[str] = None 
    description: Optional[str] = None

class LearningOutcome(BaseModel):
    skill_name: str
    target_level: SkillLevel = SkillLevel.INTERMEDIATE
    achieved_competencies: List[str] = []

    @field_validator('achieved_competencies', mode='before')
    @classmethod
    def validate_list(cls, v):
        return ensure_list(v)

class RoadmapStep(BaseModel):
    order: int = Field(..., ge=1)
    title: str
    description: str
    linked_skill_gaps: List[str] = [] 
    focus_skills: List[str] = []
    estimated_duration: str 
    key_topics: List[str] = []
    resources: List[LearningResource] = []
    ui_color: str = "primary"
    is_completed: bool = False

    @field_validator('linked_skill_gaps', 'focus_skills', 'key_topics', 'resources', mode='before')
    @classmethod
    def validate_lists(cls, v):
        return ensure_list(v)

class LearningRoadmapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    roadmap_id: Optional[str] = None
    target_job_title: str
    summary: str = Field(..., description="Overview of the learning journey")
    difficulty: str = "Intermediate"
    estimated_total_time: str 
    steps: List[RoadmapStep] = []
    final_outcomes: List[LearningOutcome] = []
    mentor_advice: Optional[str] = None

    @field_validator('steps', 'final_outcomes', mode='before')
    @classmethod
    def validate_main_lists(cls, v):
        return ensure_list(v)