"""
External Job Opportunity Matcher
================================

Matches a parsed Resume against a real external JobOpportunity.

This matcher is intentionally separate from MatchingEngine.

MatchingEngine:
    Resume <-> user supplied Job

OpportunityMatcher:
    Resume <-> real external JobOpportunity
"""

import logging
import re

logger = logging.getLogger("ResumeAnalyzer")


class OpportunityMatcher:
    """
    Matches a Resume against a real external job posting.
    """

    def __init__(self):
        logger.info("Opportunity Matcher initialized.")

    # ==========================================================
    # PUBLIC MATCH METHOD
    # ==========================================================

    def match(self, resume, opportunity):
        """
        Calculate resume match information for a JobOpportunity.

        Returns:
            dict containing:

            - match_score
            - matched_skills
            - missing_skills
            - why_suitable
        """

        resume_skills = self._normalize_skills(
            getattr(resume, "skills", [])
        )

        job_text = self._job_to_text(
            opportunity
        )

        matched_skills = []

        for skill in resume_skills:

            if skill and skill in job_text:
                matched_skills.append(skill)

        matched_skills = sorted(
            matched_skills
        )[:10]

        missing_skills = sorted(
            resume_skills -
            set(matched_skills)
        )[:8]

        # ------------------------------------------------------
        # Calculate score
        # ------------------------------------------------------

        if resume_skills:

            score = (
                len(matched_skills)
                /
                len(resume_skills)
                * 100
            )

        else:

            score = 0

        score = round(
            min(score, 100),
            1
        )

        # ------------------------------------------------------
        # Why suitable
        # ------------------------------------------------------

        why_suitable = (
            self._build_reason(
                score
            )
        )

        logger.info(
            "Opportunity matched. "
            "title='%s' score=%s matched=%s",
            getattr(
                opportunity,
                "title",
                "",
            ),
            score,
            matched_skills,
        )

        return {
            "match_score": score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "why_suitable": why_suitable,
        }

    # ==========================================================
    # NORMALIZE SKILLS
    # ==========================================================

    @staticmethod
    def _normalize_skills(skills):

        if not skills:
            return set()

        normalized = set()

        for skill in skills:

            if not isinstance(
                skill,
                str
            ):
                continue

            skill = (
                skill
                .strip()
                .lower()
            )

            if skill:
                normalized.add(skill)

        return normalized

    # ==========================================================
    # JOB TEXT
    # ==========================================================

    @staticmethod
    def _job_to_text(opportunity):

        values = [
            getattr(
                opportunity,
                "title",
                "",
            ),

            getattr(
                opportunity,
                "description",
                "",
            ),

            getattr(
                opportunity,
                "company",
                "",
            ),

            getattr(
                opportunity,
                "location",
                "",
            ),
        ]

        return " ".join(
            str(value).lower()
            for value in values
            if value
        )

    # ==========================================================
    # REASON
    # ==========================================================

    @staticmethod
    def _build_reason(score):

        if score >= 75:

            return (
                "Strong alignment with the "
                "skills detected in your resume."
            )

        if score >= 50:

            return (
                "Good potential match with "
                "several relevant resume skills."
            )

        if score >= 30:

            return (
                "Some of your skills match this "
                "role, but additional skills may "
                "be required."
            )

        return (
            "Limited direct skill overlap. "
            "Review the requirements before applying."
        )