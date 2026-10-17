import os
import sys
import json

# ----------------------------------------------------
# Add Project Root to Python Path
# ----------------------------------------------------

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

sys.path.insert(0, PROJECT_ROOT)

# ----------------------------------------------------

from app.analysis.career_analysis_service import (
    CareerAnalysisService,
)


def main():

    print("=" * 70)
    print("UNIFIED AI CAREER ANALYSIS")
    print("=" * 70)

    service = CareerAnalysisService()

    report = service.analyze(

        resume_path="sample_resume.pdf",

        company="Google",

        role="Backend Engineer",

    )

    # report is already a dictionary
    print(json.dumps(report, indent=4))

    print()

    print("=" * 70)
    print("PIPELINE EXECUTED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()