from app.career.skill_gap_service import SkillGapService


class SkillGapAnalyzer:
    """
    Backward-compatible wrapper around SkillGapService.

    Existing parts of the application can continue using:

        SkillGapAnalyzer.analyze(...)

    while the actual Skill Gap logic lives in SkillGapService.
    """

    @staticmethod
    def analyze(
        resume_skills,
        job_skills,
        target_role=None,
    ):
        """
        Analyze the skill gap between resume and target job.

        Returns a dictionary for backward compatibility
        with the existing AnalysisPipeline.
        """

        service = SkillGapService()

        result = service.analyze(
            resume_skills=resume_skills or [],
            target_skills=job_skills or [],
            target_role=target_role,
        )

        return {
            "score": service.calculate_match_score(
                resume_skills=resume_skills or [],
                target_skills=job_skills or [],
            ),

            "matched": result.matched_skills,

            "partial": result.partial_skills,

            "missing": result.missing_skills,

            "additional": sorted(
                set(
                    service.normalize_skills(
                        resume_skills or []
                    )
                )
                - set(
                    service.normalize_skills(
                        job_skills or []
                    )
                )
            ),

            "priority_gaps": [
                gap.model_dump()
                for gap in result.priority_gaps
            ],

            "recommended_actions":
                result.recommended_actions,

            "target_role":
                result.target_role,
        }