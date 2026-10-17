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

    print("\nRESULT:")
    print(result.model_dump())

    assert "python" in result.matched_skills
    assert "sql" in result.matched_skills
    assert "fastapi" in result.matched_skills

    assert "aws" in result.missing_skills
    assert "kubernetes" in result.missing_skills
    assert "ci/cd" in result.missing_skills


def test_skill_normalization():

    service = SkillGapService()

    assert service.normalize_skill("Python Programming") == "python"
    assert service.normalize_skill("GitHub") == "git"
    assert service.normalize_skill("AWS") == "aws"
    assert service.normalize_skill("K8s") == "kubernetes"


def test_skill_match_score():

    service = SkillGapService()

    score = service.calculate_match_score(
        resume_skills=[
            "Python",
            "SQL",
        ],
        target_skills=[
            "Python",
            "SQL",
            "AWS",
            "Docker",
        ],
    )

    assert score == 50.0