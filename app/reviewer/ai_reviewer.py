from app.services.ai_service import AIService
from app.core.prompts import AI_REVIEW_PROMPT
from app.models.review import Review
from app.validators.review_validator import ReviewValidator


class AIReviewer:
    """
    Uses AI to review a resume and generate
    strengths, weaknesses, and suggestions.
    """

    def __init__(self):
        self.ai_service = AIService()

    def review(self, resume_text):
        """
        Reviews the resume using AI.
        """

        prompt = AI_REVIEW_PROMPT.format(
            resume=resume_text
        )

        response = self.ai_service.send_json_prompt(
            prompt
        )

        # If the AIService somehow returns a JSON string,
        # convert it into a dictionary.
        if isinstance(response, str):
            import json

            response = json.loads(response)

        validated = ReviewValidator.validate(
            response
        )

        return Review.from_dict(
            validated
        )