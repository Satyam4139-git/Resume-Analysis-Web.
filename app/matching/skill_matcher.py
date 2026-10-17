from __future__ import annotations

from typing import Any


class SkillMatcher:
    """
    Deterministic skill matching utility.

    Safely handles both normal strings and AI-generated
    dictionary-style skill objects.
    """

    @staticmethod
    def _extract_skill(
        skill: Any,
    ) -> str:

        if skill is None:
            return ""

        if isinstance(
            skill,
            str,
        ):
            return skill.strip().lower()

        if isinstance(
            skill,
            dict,
        ):

            for key in (
                "name",
                "skill",
                "title",
                "value",
                "text",
            ):

                value = skill.get(
                    key
                )

                if value:
                    return str(
                        value
                    ).strip().lower()

            return ""

        return str(
            skill
        ).strip().lower()

    @classmethod
    def _normalize(
        cls,
        skills,
    ):

        if skills is None:
            return set()

        if isinstance(
            skills,
            (str, dict),
        ):
            skills = [
                skills
            ]

        result = set()

        for skill in skills:

            normalized = cls._extract_skill(
                skill
            )

            if normalized:
                result.add(
                    normalized
                )

        return result

    @classmethod
    def match(
        cls,
        resume_skills,
        job_skills,
    ):

        resume = cls._normalize(
            resume_skills
        )

        job = cls._normalize(
            job_skills
        )

        matched = sorted(
            resume.intersection(
                job
            )
        )

        missing = sorted(
            job.difference(
                resume
            )
        )

        # No job requirements means there is no meaningful
        # skill match percentage.
        score = (
            round(
                len(matched)
                / len(job)
                * 100
            )
            if job
            else 0
        )

        return {
            "score": max(
                0,
                min(
                    100,
                    score,
                ),
            ),

            "matched": matched,

            "missing": missing,

            "matched_count": len(
                matched
            ),

            "required_count": len(
                job
            ),
        }