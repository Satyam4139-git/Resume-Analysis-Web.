from app.career.job_recommendation_engine import (
    JobRecommendationEngine
)

from app.models.resume import Resume


def main():

    # ==========================================================
    # CREATE TEST RESUME
    # ==========================================================

    resume = Resume(

        name="Test User",

        email="test@example.com",

        skills=[
            "Python",
            "FastAPI",
            "Git",
            "SQL",
            "Docker"
        ],

        experience="1 year",

        education=[
            "B.Tech"
        ],

        projects=[
            "AI Resume Analyzer"
        ],

        summary=(
            "Python backend developer "
            "with FastAPI experience."
        )
    )

    # ==========================================================
    # CREATE ENGINE
    # ==========================================================

    engine = JobRecommendationEngine()

    # ==========================================================
    # GENERATE RECOMMENDATIONS
    # ==========================================================

    recommendations = engine.recommend(
        resume
    )

    # ==========================================================
    # DISPLAY RESULTS
    # ==========================================================

    print("\n")
    print("=" * 70)
    print("JOB RECOMMENDATIONS")
    print("=" * 70)

    for index, recommendation in enumerate(
        recommendations,
        start=1
    ):

        print("\n")

        print(
            f"{index}. "
            f"{recommendation['role']}"
        )

        print(
            f"Match Score: "
            f"{recommendation['match_score']}%"
        )

        print(
            "Matched Skills:",
            ", ".join(
                recommendation[
                    "matched_skills"
                ]
            )
        )

        print(
            "Missing Skills:",
            ", ".join(
                recommendation[
                    "missing_skills"
                ]
            )
        )

        print(
            "Reason:",
            recommendation[
                "reason"
            ]
        )

    print("\n")
    print("=" * 70)
    print(
        "TOTAL RECOMMENDATIONS:",
        len(recommendations)
    )
    print("=" * 70)


if __name__ == "__main__":

    main()