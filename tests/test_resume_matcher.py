from app.matching import ResumeMatcher
from app.models.resume import Resume
from app.models.job import Job


def main():
    # -------------------------
    # Create Sample Resume
    # -------------------------
    resume = Resume(
        name="John Doe",
        email="john@example.com",
        phone="1234567890",
        summary="Backend Developer",
        skills=[
            "Python",
            "SQL",
            "Docker",
            "Git"
        ],
        experience=[],
        education=[],
        projects=[],
        resume_score=0
    )

    # -------------------------
    # Create Sample Job
    # -------------------------
    job = Job(
        title="Backend Engineer",
        company="Google",
        skills=[
            "Python",
            "Docker",
            "AWS",
            "Git",
            "Kubernetes"
        ],
        experience_required="2 Years"
    )

    # -------------------------
    # Match Resume
    # -------------------------
    matcher = ResumeMatcher()

    result = matcher.match(
        resume,
        job
    )

    print("\n" + "=" * 60)
    print("RESUME MATCH REPORT")
    print("=" * 60)

    print(f"Match Score : {result['match_score']}%")

    print("\nMatched Skills")
    print("----------------")
    for skill in result["matched_skills"]:
        print(f"✓ {skill}")

    print("\nMissing Skills")
    print("----------------")
    for skill in result["missing_skills"]:
        print(f"✗ {skill}")

    print("\nExtra Skills")
    print("----------------")
    for skill in result["extra_skills"]:
        print(f"+ {skill}")

    print("\nRecommendation")
    print("----------------")
    print(result["recommendation"])


if __name__ == "__main__":
    main()