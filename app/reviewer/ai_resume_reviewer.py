import json
import logging

from app.core.config import AI_REVIEW_MAX_TOKENS, AI_REVIEW_BUDGET_SECONDS
from app.services.ai_service import AIService
from app.models.resume import Resume
from app.models.review import Review
from app.validators.review_validator import ReviewValidator
from app.core.prompts import AI_REVIEW_PROMPT

logger = logging.getLogger("ResumeAnalyzer")


class AIResumeReviewer:
    """
    AI-powered resume reviewer.

    Responsibilities:
    - Receive a parsed Resume object
    - Convert resume data into reviewable text
    - Send the resume to the AI service
    - Request structured JSON output
    - Validate the AI response
    - Convert validated data into a Review model
    """

    def __init__(self):
        """
        Initialize the AI Resume Reviewer.
        """
        self.ai = AIService()

        logger.info(
            "AI Resume Reviewer initialized. "
            "Max tokens: %s",
            AI_REVIEW_MAX_TOKENS,
        )

    # ==========================================================
    # RESUME TO TEXT
    # ==========================================================

    @staticmethod
    def _resume_to_text(resume):
        """
        Convert a Resume object into a compact text representation
        for the AI reviewer.
        """

        if isinstance(resume, Resume):
            return json.dumps(resume.to_dict(), ensure_ascii=False)[:6000]
        elif isinstance(resume, dict):
            resume_data = resume
        else:
            raise TypeError(
                "resume must be a Resume object or dictionary."
            )

        return str(resume_data)

    # ==========================================================
    # REVIEW
    # ==========================================================

    def review(self, resume):
        """
        Review a resume using AI.

        Parameters
        ----------
        resume : Resume
            Parsed Resume object.

        Returns
        -------
        Review
            Validated Review model.
        """

        logger.info(
            "AI Resume Reviewer started."
        )

        # ------------------------------------------------------
        # Validate input
        # ------------------------------------------------------

        if resume is None:
            raise ValueError(
                "Resume cannot be None."
            )

        # ------------------------------------------------------
        # Convert Resume object to text
        # ------------------------------------------------------

        try:
            resume_text = self._resume_to_text(
                resume
            )
        except Exception as error:
            logger.exception(
                "Failed to convert resume to text."
            )
            raise RuntimeError(
                f"Failed to prepare resume for AI review: {error}"
            ) from error

        if not resume_text.strip():
            raise ValueError(
                "Resume contains no data to review."
            )

        # ------------------------------------------------------
        # Build AI review prompt
        # ------------------------------------------------------

        try:
            prompt = AI_REVIEW_PROMPT.format(
                resume=resume_text
            )
        except Exception as error:
            logger.exception(
                "Failed to build AI review prompt."
            )
            raise RuntimeError(
                f"Failed to build AI review prompt: {error}"
            ) from error

        # ------------------------------------------------------
        # Send request to AI
        # ------------------------------------------------------

        logger.info(
            "Sending resume to AI for review."
        )

        try:
            data = self.ai.send_json_prompt(
                prompt,
                max_tokens=min(AI_REVIEW_MAX_TOKENS, 900),
                budget=AI_REVIEW_BUDGET_SECONDS,
            )

        except Exception as error:
            logger.exception(
                "AI resume review failed."
            )
            raise

        # ------------------------------------------------------
        # Validate AI response
        # ------------------------------------------------------

        if not isinstance(data, dict):
            logger.error(
                "AI reviewer returned invalid data type: %s",
                type(data),
            )

            raise RuntimeError(
                "AI reviewer did not return a valid JSON object."
            )

        logger.info(
            "AI resume review JSON received successfully."
        )

        # ------------------------------------------------------
        # Validate review structure
        # ------------------------------------------------------

        try:
            validated_data = ReviewValidator.validate(
                data
            )

        except Exception as error:
            logger.exception(
                "AI review validation failed."
            )

            raise RuntimeError(
                f"AI review validation failed: {error}"
            ) from error

        # ------------------------------------------------------
        # Convert validated data to Review model
        # ------------------------------------------------------

        try:
            review = Review.from_dict(
                validated_data
            )

        except Exception as error:
            logger.exception(
                "Failed to create Review model."
            )

            raise RuntimeError(
                f"Failed to create Review model: {error}"
            ) from error

        logger.info(
            "AI Resume Review created successfully."
        )

        return review