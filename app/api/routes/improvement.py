from fastapi import APIRouter

from app.improver.improvement_service import ImprovementService
from app.models.resume import Resume

router = APIRouter()

service = ImprovementService()


@router.post("/improve")
def improve_resume(resume: dict):

    resume_obj = Resume.from_dict(resume)

    result = service.improve(resume_obj)

    return result.to_dict()