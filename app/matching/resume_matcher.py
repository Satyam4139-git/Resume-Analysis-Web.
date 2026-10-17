from typing import Dict, List
import logging

from app.ats import ATSScorer

logger = logging.getLogger("ResumeAnalyzer")


class ResumeMatcher:
    """
    Matches a candidate's resume against a target job profile.
    """

    def __init__(self):
        logger.info("ResumeMatcher initialized.")

    @staticmethod
    def _normalize(skills: List[str]) -> List[str]:
        """
        Normalize skills by converting to lowercase,
        removing duplicates, and stripping whitespace.
        """
        normalized = {
            skill.strip().lower()
            for skill in skills
            if skill.strip()
        }

        return sorted(normalized)

    def match(self, resume, job) -> Dict:
        """
        Compare resume skills with job skills.

        Parameters
        ----------
        resume : Resume
            Resume object

        job : Job
            Job object

        Returns
        -------
        dict
            Matching report
        """

        logger.info("Starting resume matching.")

        resume_skills = self._normalize(resume.skills)
        job_skills = self._normalize(job.skills)

        matched_skills = sorted(
            list(set(resume_skills) & set(job_skills))
        )

        missing_skills = sorted(
            list(set(job_skills) - set(resume_skills))
        )

        extra_skills = sorted(
            list(set(resume_skills) - set(job_skills))
        )

        if len(job_skills) == 0:
            score = 0.0
        else:
            score = round(
                (len(matched_skills) / len(job_skills)) * 100,
                2,
            )

        if score >= 90:
            recommendation = (
                "Excellent match. Your resume closely matches the job requirements."
            )

        elif score >= 70:
            recommendation = (
                "Good match. Improve a few missing skills to become a stronger candidate."
            )

        elif score >= 50:
            recommendation = (
                "Average match. Learning the missing skills will significantly improve your chances."
            )

        else:
            recommendation = (
                "Low match. Focus on acquiring the required technical skills before applying."
            )

        logger.info("Resume matching completed successfully.")

        result = {
            "match_score": score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "extra_skills": extra_skills,
            "recommendation": recommendation,
        }

        # Preserve the original matching response while providing a complete,
        # explainable ATS assessment for the same resume/job pair.
        result["ats_report"] = ATSScorer().score(resume, job).to_dict()
        return result
