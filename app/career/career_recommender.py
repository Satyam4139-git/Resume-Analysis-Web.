from app.career.recommendation_models import (
    CareerRecommendation,
)

from app.career.recommendation_rules import (
    PROJECT_RULES,
)


class CareerRecommender:
    """
    Generates career recommendations.
    """

    @staticmethod
    def recommend(
        role,
        ats_score,
        missing_skills,
    ):

        role_key = role.lower()

        project = PROJECT_RULES.get(
            role_key,
            PROJECT_RULES["default"],
        )

        readiness = ats_score

        estimated_weeks = (
            len(missing_skills) * 2
        )

        if estimated_weeks == 0:
            estimated_weeks = 1

        summary = (
            f"You are approximately "
            f"{readiness}% ready for the "
            f"{role} role."
        )

        return CareerRecommendation(

            role=role,

            readiness=readiness,

            estimated_weeks=estimated_weeks,

            priority_skills=missing_skills,

            recommended_project=project,

            summary=summary,
        )