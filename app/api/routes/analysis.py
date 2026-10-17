import os

from fastapi import APIRouter, HTTPException

from app.analysis.career_analysis_service import (
    CareerAnalysisService
)

from app.api.schemas.request import AIExtrasRequest, AnalysisRequest


router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"]
)


service = CareerAnalysisService()


@router.post("/")
def analyze(
    request: AnalysisRequest
):
    """
    Run resume-first career analysis.

    Company, role and job description are optional.
    """

    # ======================================================
    # STEP 1 — VALIDATE RESUME PATH
    # ======================================================

    if not request.resume_path:

        raise HTTPException(
            status_code=400,
            detail="resume_path is required."
        )

    if (
        request.resume_path
        .strip()
        .lower()
        == "string"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid resume_path. "
                "Send the actual resume_path returned "
                "by POST /resume/upload."
            )
        )

    # ======================================================
    # STEP 2 — FILE EXISTS
    # ======================================================

    if not os.path.isfile(
        request.resume_path
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                f"Resume file not found: "
                f"{request.resume_path}"
            )
        )

    # ======================================================
    # STEP 3 — ANALYSIS
    # ======================================================

    try:

        result = service.analyze(

            resume_path=request.resume_path,

            company=request.company,

            role=request.role,

            job_description=(
                request.job_description
            ),

        )

        return result

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {error}"
        ) from error


@router.post("/ai")
def analyze_ai(
    request: AIExtrasRequest
):
    """
    Slower AI part of the analysis: resume review and improvement tips.
    """

    path = (request.resume_path or "").strip()

    if not path or path.lower() == "string" or not os.path.isfile(path):

        raise HTTPException(
            status_code=404,
            detail="Resume file not found. Upload the resume again.",
        )

    try:

        return service.analyze_ai(path)

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"AI review failed: {error}"
        ) from error
