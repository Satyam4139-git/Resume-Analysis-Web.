import os
import shutil
import uuid

from fastapi import APIRouter, File, UploadFile, HTTPException

from app.parser.resume_parser import ResumeParser
from app.exceptions.custom_exceptions import ResumeParserError


router = APIRouter(
    prefix="/resume",
    tags=["Resume"]
)


UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...)
):
    """
    Upload a resume, save it to the uploads folder,
    parse it using AI, and return the parsed resume
    together with the saved file path.
    """

    # ==========================================================
    # STEP 1 — VALIDATE FILE
    # ==========================================================

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was provided."
        )

    allowed_extensions = {
        ".pdf",
        ".docx"
    }

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported."
        )

    # ==========================================================
    # STEP 2 — CREATE SAFE UNIQUE FILE NAME
    # ==========================================================

    original_filename = file.filename

    unique_filename = (
        f"{uuid.uuid4().hex}{extension}"
    )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        unique_filename
    )

    # ==========================================================
    # STEP 3 — SAVE FILE
    # ==========================================================

    try:

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {error}"
        ) from error

    # ==========================================================
    # STEP 4 — PARSE RESUME
    # ==========================================================

    parser = ResumeParser()

    try:

        resume = parser.parse(
            file_path
        )

    except ResumeParserError as error:

        # Remove failed upload
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=502,
            detail=(
                "The AI provider returned an incomplete "
                "or invalid resume response. Please try again."
            )
        ) from error

    except Exception as error:

        # Remove failed upload
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=f"Resume parsing failed: {error}"
        ) from error

    # ==========================================================
    # STEP 5 — VALIDATE RESULT
    # ==========================================================

    if resume is None:

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail="Resume parsing failed."
        )

    # ==========================================================
    # STEP 6 — RETURN RESULT
    # ==========================================================

    return {

        "success": True,

        "message": "Resume uploaded successfully.",

        "filename": original_filename,

        "stored_filename": unique_filename,

        "resume_path": file_path,

        "resume": resume.to_dict()

    }