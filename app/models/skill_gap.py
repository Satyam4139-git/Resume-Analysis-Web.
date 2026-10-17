from typing import List, Optional
from pydantic import BaseModel, Field


class SkillGap(BaseModel):
    skill: str
    priority: str = "medium"
    reason: Optional[str] = None


class SkillGapResult(BaseModel):
    target_role: Optional[str] = None

    matched_skills: List[str] = Field(default_factory=list)
    partial_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)

    priority_gaps: List[SkillGap] = Field(default_factory=list)

    recommended_actions: List[str] = Field(default_factory=list)