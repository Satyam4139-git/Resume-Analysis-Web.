from fastapi import APIRouter

from app.reviewer.review_service import ReviewService
from app.models.resume import Resume

router = APIRouter()

service = ReviewService()


@router.post("/review")
def review_resume(resume: dict):

    resume_obj = Resume.from_dict(resume)

    review = service.review(resume_obj)

    return review.to_dict()