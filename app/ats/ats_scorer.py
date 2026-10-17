"""
Deterministic ATS / Resume scoring engine.

AI extracts information.

This class calculates the resume score.
"""

import logging

from app.ats.scoring_rules import (
    RESUME_SCORE_WEIGHTS,
)

logger = logging.getLogger(
    "ResumeAnalyzer"
)


class ATSScorer:
    """
    Calculates a deterministic resume score.

    AI should extract information.
    This class calculates the score.
    """

    def __init__(self):

        logger.info(
            "ATS Scorer initialized."
        )

    # ==========================================================
    # MAIN SCORE
    # ==========================================================

    def score_resume(self, resume):
        """
        Calculate overall resume score.

        Returns
        -------
        dict
        """

        skills_score = (
            self._score_skills(resume)
        )

        projects_score = (
            self._score_projects(resume)
        )

        experience_score = (
            self._score_experience(resume)
        )

        education_score = (
            self._score_education(resume)
        )

        ats_score = (
            self._score_ats_compatibility(
                resume
            )
        )

        overall_score = round(
            (
                skills_score
                * RESUME_SCORE_WEIGHTS[
                    "skills"
                ]
                +
                projects_score
                * RESUME_SCORE_WEIGHTS[
                    "projects"
                ]
                +
                experience_score
                * RESUME_SCORE_WEIGHTS[
                    "experience"
                ]
                +
                education_score
                * RESUME_SCORE_WEIGHTS[
                    "education"
                ]
                +
                ats_score
                * RESUME_SCORE_WEIGHTS[
                    "ats_compatibility"
                ]
            )
            / 100
        )

        grade = self._calculate_grade(
            overall_score
        )

        result = {
            "score": overall_score,
            "grade": grade,
            "breakdown": {
                "skills": skills_score,
                "projects": projects_score,
                "experience": experience_score,
                "education": education_score,
                "ats_compatibility": ats_score,
            },
        }

        logger.info(
            "Resume ATS score calculated: %s",
            overall_score,
        )

        return result

    # ==========================================================
    # SKILLS
    # ==========================================================

    def _score_skills(self, resume):

        skills = getattr(
            resume,
            "skills",
            [],
        ) or []

        if not skills:
            return 0

        count = len(skills)

        if count >= 10:
            return 100

        if count >= 7:
            return 85

        if count >= 4:
            return 70

        if count >= 2:
            return 50

        return 25

    # ==========================================================
    # PROJECTS
    # ==========================================================

    def _score_projects(self, resume):

        projects = getattr(
            resume,
            "projects",
            [],
        ) or []

        if not projects:
            return 0

        count = len(projects)

        if count >= 4:
            return 100

        if count == 3:
            return 85

        if count == 2:
            return 70

        return 45

    # ==========================================================
    # EXPERIENCE
    # ==========================================================

    def _score_experience(self, resume):

        experience = getattr(
            resume,
            "experience",
            None,
        )

        if not experience:
            return 40

        if isinstance(
            experience,
            str,
        ):

            length = len(
                experience.strip()
            )

            if length < 50:
                return 50

            if length < 150:
                return 70

            return 90

        if isinstance(
            experience,
            list,
        ):

            if len(experience) == 0:
                return 40

            if len(experience) >= 3:
                return 100

            if len(experience) == 2:
                return 85

            return 70

        return 60

    # ==========================================================
    # EDUCATION
    # ==========================================================

    def _score_education(self, resume):

        education = getattr(
            resume,
            "education",
            [],
        ) or []

        if not education:
            return 0

        if len(education) >= 2:
            return 100

        return 85

    # ==========================================================
    # ATS COMPATIBILITY
    # ==========================================================

    def _score_ats_compatibility(
        self,
        resume,
    ):
        """
        Basic deterministic ATS compatibility score.
        """

        score = 0

        skills = getattr(
            resume,
            "skills",
            [],
        ) or []

        projects = getattr(
            resume,
            "projects",
            [],
        ) or []

        summary = getattr(
            resume,
            "summary",
            "",
        ) or ""

        education = getattr(
            resume,
            "education",
            [],
        ) or []

        name = getattr(
            resume,
            "name",
            "",
        ) or ""

        email = getattr(
            resume,
            "email",
            "",
        ) or ""

        phone = getattr(
            resume,
            "phone",
            "",
        ) or ""

        # ------------------------------------------------------
        # Skills
        # ------------------------------------------------------

        if skills:
            score += 25

        # ------------------------------------------------------
        # Projects
        # ------------------------------------------------------

        if projects:
            score += 20

        # ------------------------------------------------------
        # Summary
        # ------------------------------------------------------

        if summary:
            score += 15

        # ------------------------------------------------------
        # Education
        # ------------------------------------------------------

        if education:
            score += 15

        # ------------------------------------------------------
        # Name
        # ------------------------------------------------------

        if name:
            score += 5

        # ------------------------------------------------------
        # Email
        # ------------------------------------------------------

        if email:
            score += 5

        # ------------------------------------------------------
        # Phone
        # ------------------------------------------------------

        if phone:
            score += 5

        # ------------------------------------------------------
        # Experience
        # ------------------------------------------------------

        experience = getattr(
            resume,
            "experience",
            None,
        )

        if experience:
            score += 10

        return min(
            100,
            score,
        )

    # ==========================================================
    # GRADE
    # ==========================================================

    def _calculate_grade(
        self,
        score,
    ):

        if score >= 90:
            return "A+"

        if score >= 80:
            return "A"

        if score >= 70:
            return "B"

        if score >= 60:
            return "C"

        if score >= 50:
            return "D"

        return "F"