import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

sys.path.insert(0, PROJECT_ROOT)

from app.reviewer.review_service import ReviewService


def main():

    resume_text = """

John Doe

Python Developer

Skills:
Python
FastAPI
Git
SQL

Experience:
2 Years Backend Development

Projects:
AI Resume Analyzer
E-Commerce API

Education:
B.Tech Computer Science

"""

    service = ReviewService()

    review = service.review_resume(resume_text)

    print("=" * 60)
    print("AI RESUME REVIEW")
    print("=" * 60)

    print("\nStrengths")

    for item in review.strengths:
        print(f"✔ {item}")

    print("\nWeaknesses")

    for item in review.weaknesses:
        print(f"✘ {item}")

    print("\nSuggestions")

    for item in review.suggestions:
        print(f"- {item}")


if __name__ == "__main__":
    main()