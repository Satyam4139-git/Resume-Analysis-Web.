from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.tracker.application_service import (
    ApplicationService,
)


router = APIRouter(
    prefix="/applications",
    tags=["Application Tracker"],
)

service = ApplicationService()


def current_user_id(request: Request) -> str:
    """Tracker data is private: only signed-in users, and only their own."""

    user = request.session.get("user") or {}
    user_id = user.get("id") or user.get("email")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Please sign in to use the application tracker.",
        )

    return str(user_id)


@router.post("/")
def create_application(
    request: dict,
    user_id: str = Depends(current_user_id),
):

    try:

        application = service.create(
            user_id=user_id,
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
    user_id: str = Depends(current_user_id),
):

    try:

        applications = service.get_all(
            user_id,
            status=status,
        )

        return {
            "success": True,
            "applications": applications,
            "statistics": service.statistics(user_id),
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Could not load applications: {error}",
        ) from error


@router.get("/statistics")
def application_statistics(
    user_id: str = Depends(current_user_id),
):

    return {
        "success": True,
        "statistics": service.statistics(user_id),
    }


@router.put("/{application_id}")
def update_application(
    application_id: int,
    request: dict,
    user_id: str = Depends(current_user_id),
):

    try:

        application = service.update(
            user_id=user_id,
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
    user_id: str = Depends(current_user_id),
):

    try:

        deleted = service.delete(
            user_id,
            application_id,
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