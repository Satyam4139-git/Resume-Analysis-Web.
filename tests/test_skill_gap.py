from app.career.skill_gap_service import SkillGapService


def test_skill_gap():

    service = SkillGapService()

    resume_skills = [
        "Python",
        "SQL",
        "FastAPI",
        "Git",
        "Docker",
    ]

    target_skills = [
        "Python",
        "SQL",
        "FastAPI",
        "Docker",
        "AWS",
        "Kubernetes",
        "CI/CD",
    ]

    result = service.analyze(
        resume_skills=resume_skills,
        target_skills=target_skills,
        target_role="Backend Developer",
    )

    print(result.model_dump())

    assert "python" in result.matched_skills
    assert "sql" in result.matched_skills
    assert "aws" in result.missing_skills
    assert "kubernetes" in result.missing_skills