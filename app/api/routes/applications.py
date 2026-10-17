from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.tracker.application_service import (
    ApplicationService,
)


router = APIRouter(
    prefix="/applications",
    tags=["Application Tracker"],
)

service = ApplicationService()


@router.post("/")
def create_application(request: dict):

    try:

        application = service.create(
            company=request.get(
                "company",
                "",
            ),
            role=request.get(
                "role",
                "",
            ),
            job_url=request.get(
                "job_url"
            ),
            status=request.get(
                "status",
                "Applied",
            ),
            applied_date=request.get(
                "applied_date"
            ),
            notes=request.get(
                "notes"
            ),
        )

        return {
            "success": True,
            "application": application,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.get("/")
def list_applications(
    status: str | None = None,
):

    try:

        applications = service.get_all(
            status=status
        )

        return {
            "success": True,
            "applications": applications,
            "statistics": service.statistics(),
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Could not load applications: {error}",
        ) from error


@router.get("/statistics")
def application_statistics():

    return {
        "success": True,
        "statistics": service.statistics(),
    }


@router.put("/{application_id}")
def update_application(
    application_id: int,
    request: dict,
):

    try:

        application = service.update(
            application_id=application_id,
            company=request.get("company"),
            role=request.get("role"),
            job_url=request.get("job_url"),
            status=request.get("status"),
            applied_date=request.get(
                "applied_date"
            ),
            notes=request.get("notes"),
        )

        return {
            "success": True,
            "application": application,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.delete("/{application_id}")
def delete_application(
    application_id: int,
):

    try:

        deleted = service.delete(
            application_id
        )

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Application not found.",
            )

        return {
            "success": True,
            "message": "Application deleted.",
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Delete failed: {error}",
        ) from error