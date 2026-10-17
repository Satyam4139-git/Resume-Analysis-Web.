"""
Scoring rules used by the ATS and resume scoring engine.

All scoring is deterministic.
AI is NOT responsible for calculating scores.
"""


# ============================================================
# RESUME SCORE
# ============================================================

RESUME_SCORE_WEIGHTS = {
    "skills": 25,
    "projects": 20,
    "experience": 20,
    "education": 15,
    "ats_compatibility": 20,
}


# ============================================================
# JOB MATCH SCORE
# ============================================================

JOB_MATCH_WEIGHTS = {
    "skills": 40,
    "keywords": 20,
    "experience": 20,
    "education": 10,
    "project_relevance": 10,
}


# ============================================================
# JOB RECOMMENDATION
# ============================================================

JOB_RECOMMENDATION_THRESHOLD = 50


# ============================================================
# SKILL COVERAGE
# ============================================================

SKILL_COVERAGE_THRESHOLDS = {
    "excellent": 80,
    "good": 65,
    "moderate": 50,
    "low": 0,
}


# ============================================================
# COMPONENT THRESHOLDS
# ============================================================

SKILL_THRESHOLDS = {
    "excellent": 10,
    "good": 7,
    "moderate": 4,
    "low": 0,
}

PROJECT_THRESHOLDS = {
    "excellent": 4,
    "good": 3,
    "moderate": 2,
    "low": 0,
}