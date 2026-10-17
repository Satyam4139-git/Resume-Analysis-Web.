from typing import Optional

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """
    Request for resume-first career analysis.

    A specific company/job is optional.
    If supplied, the system also performs
    target-job matching.
    """

    resume_path: str = Field(
        ...,
        description="Path returned by the resume upload endpoint."
    )

    company: Optional[str] = Field(
        default=None,
        description="Optional target company."
    )

    role: Optional[str] = Field(
        default=None,
        description="Optional target role."
    )

    job_description: Optional[str] = Field(
        default=None,
        description="Optional target job description."
    )

    include_ai: bool = Field(
        default=True,
        description=(
            "False returns the main results quickly and leaves the AI "
            "review / improvement tips for POST /analysis/ai."
        ),
    )


class AIExtrasRequest(BaseModel):
    resume_path: str = Field(
        ...,
        description="Path returned by the resume upload endpoint."
    )
