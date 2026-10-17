import os
import sys
import json

# ----------------------------------------------------
# Add project root to Python path
# ----------------------------------------------------

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

sys.path.insert(0, PROJECT_ROOT)

# ----------------------------------------------------
# Imports
# ----------------------------------------------------

from app.models.resume import Resume
from app.models.job import Job

from app.matching.matching_engine import MatchingEngine

# ----------------------------------------------------
# Main Test
# ----------------------------------------------------


def main():

    print("=" * 60)
    print("AI RESUME ANALYZER - ATS ENGINE TEST")
    print("=" * 60)

    # ------------------------------------------------
    # Sample Resume
    # ------------------------------------------------

    resume = Resume(

        name="John Doe",

        email="john@gmail.com",

        phone="9876543210",

        skills=[
            "Python",
            "FastAPI",
            "Git",
            "SQL",
        ],

        experience="2 Years Backend Development",

        education=[
            "B.Tech Computer Science"
        ],

        projects=[
            "AI Resume Analyzer",
            "E-Commerce API"
        ],

        summary="Backend Python Developer"
    )

    # ------------------------------------------------
    # Sample Job
    # ------------------------------------------------

    job = Job(

        title="Backend Engineer",

        company="Google",

        skills=[
            "Python",
            "FastAPI",
            "Docker",
            "Git"
        ],

        experience_required="2 Years",

        education_required=[
            "B.Tech"
        ],

        keywords=[
            "Python",
            "REST API",
            "Microservices",
            "Docker"
        ],

        responsibilities=[
            "Develop REST APIs",
            "Write scalable backend code"
        ],

        summary="Backend Engineer"
    )

    # ------------------------------------------------
    # Compare Resume with Job
    # ------------------------------------------------

    result = MatchingEngine.compare(
        resume,
        job
    )

    # ------------------------------------------------
    # Match Result
    # ------------------------------------------------

    match_result = result["match_result"]

    ats_report = result["ats_report"]

    print("\n")

    print("=" * 60)
    print("MATCH RESULT")
    print("=" * 60)

    print(f"Overall Score      : {match_result.overall_score}")
    print(f"Skill Score        : {match_result.skill_score}")
    print(f"Keyword Score      : {match_result.keyword_score}")
    print(f"Experience Score   : {match_result.experience_score}")
    print(f"Education Score    : {match_result.education_score}")

    print()

    print("Matched Skills")

    for skill in match_result.matched_skills:
        print(f"✔ {skill}")

    print()

    print("Missing Skills")

    for skill in match_result.missing_skills:
        print(f"✘ {skill}")

    print()

    print("Suggestions")

    for suggestion in match_result.suggestions:
        print(f"- {suggestion}")

    # ------------------------------------------------
    # ATS Report
    # ------------------------------------------------

    print("\n")

    print("=" * 60)
    print("ATS REPORT")
    print("=" * 60)

    print(json.dumps(
        ats_report.to_dict(),
        indent=4
    ))

    print("\n")

    print("=" * 60)
    print("TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()