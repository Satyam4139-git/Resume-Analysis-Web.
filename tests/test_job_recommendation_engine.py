from app.career.job_recommendation_engine import JobRecommendationEngine
from app.models.resume import Resume


def main():

    print("=" * 70)
    print("TESTING JOB RECOMMENDATION ENGINE")
    print("=" * 70)

    # ==========================================================
    # CREATE TEST RESUME
    # ==========================================================

    resume = Resume(

        name="Test Candidate",

        email="test@example.com",

        phone="0000000000",

        skills=[
            "Python",
            "FastAPI",
            "Git",
            "SQL"
        ],

        experience="Backend development experience",

        education=[
            "Bachelor of Technology"
        ],

        projects=[
            "AI Resume Analyzer"
        ],

        summary=(
            "Backend-focused software developer "
            "with Python and FastAPI skills."
        )
    )

    # ==========================================================
    # CREATE ENGINE
    # ==========================================================

    engine = JobRecommendationEngine()

    # ==========================================================
    # GENERATE RECOMMENDATIONS
    # ==========================================================

    results = engine.recommend(
        resume
    )

    # ==========================================================
    # DISPLAY RESULTS
    # ==========================================================

    print()
    print("=" * 70)
    print("JOB RECOMMENDATIONS")
    print("=" * 70)

    if not results:

        print()
        print("No suitable career roles found.")

    else:

        for index, result in enumerate(
            results,
            start=1
        ):

            print()

            print(
                f"{index}. {result['role']}"
            )

            print(
                f"Match Score: "
                f"{result['match_score']}%"
            )

            print(
                f"Matched Skills: "
                f"{result['matched_skills']}"
            )

            print(
                f"Missing Skills: "
                f"{result['missing_skills']}"
            )

            print(
                f"Reason: "
                f"{result['reason']}"
            )

    print()
    print("=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":

    main()
