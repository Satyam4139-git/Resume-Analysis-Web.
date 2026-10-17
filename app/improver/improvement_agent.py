from app.core.config import AI_REVIEW_BUDGET_SECONDS
from app.services.ai_service import AIService
from app.improver.improvement_result import ImprovementResult
from app.core.prompts import RESUME_IMPROVEMENT_PROMPT
from app.core.logger import logger


class ImprovementAgent:
    """
    AI Resume Improvement Agent.

    Uses the AI provider when available and falls back to
    deterministic resume-improvement recommendations when the
    provider returns an empty or invalid response.
    """

    def __init__(self):
        self.ai = AIService()

    def improve(self, resume):

        logger.info(
            "AI Resume Improvement Agent started."
        )

        prompt = RESUME_IMPROVEMENT_PROMPT.format(
            resume=str(resume.to_dict())[:5000]
        )

        try:

            data = self.ai.send_json_prompt(
                prompt,
                max_tokens=700,
                budget=AI_REVIEW_BUDGET_SECONDS,
            )

            if not data or not isinstance(data, dict):
                raise ValueError(
                    "AI improvement returned empty or invalid data."
                )

            result = ImprovementResult.from_dict(data)

            logger.info(
                "AI Resume Improvement generated successfully."
            )

            return result

        except Exception as e:

            logger.warning(
                f"AI Improvement failed: {e}"
            )

            logger.info(
                "Using deterministic resume improvement fallback."
            )

            return ImprovementResult(
                improved_summary=(
                    resume.summary
                    if resume.summary
                    else (
                        "Create a concise professional summary that "
                        "clearly states your target role, strongest "
                        "technical skills, and measurable achievements."
                    )
                ),
                improved_skills=resume.skills,
                improved_projects=resume.projects,
                keywords_to_add=[
                    "Add keywords directly related to the target role.",
                    "Include important technologies mentioned in job descriptions.",
                    "Use standard ATS-friendly skill names.",
                ],
                ats_tips=[
                    "Use standard section headings such as Summary, Skills, Experience, Education, and Projects.",
                    "Add measurable results to important achievements.",
                    "Tailor the resume summary to the target role.",
                    "Keep technical skills clearly grouped and easy for ATS systems to parse.",
                    "Use exact technical keywords from relevant job descriptions when they genuinely match your experience.",
                ],
            )
