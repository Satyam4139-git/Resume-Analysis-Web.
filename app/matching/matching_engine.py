from __future__ import annotations

import logging
import re
from typing import Any, Dict, Iterable, List, Set

from app.ats.scoring_rules import JOB_MATCH_WEIGHTS


logger = logging.getLogger("ResumeAnalyzer")


class MatchingEngine:
    """
    Deterministic resume-to-job matching engine.

    Calculates:

        - Skill Match
        - Keyword Match
        - Experience Match
        - Education Match
        - Project Relevance
        - Overall Match Score
        - Skill Coverage
        - Matched Skills
        - Missing Skills

    The class also provides a `compare()` compatibility method
    because the AnalysisPipeline uses that API.
    """

    def __init__(self):
        logger.info("MatchingEngine initialized.")

    # =========================================================
    # PUBLIC API
    # =========================================================

    def match(self, resume, job) -> Dict[str, Any]:
        """
        Compare a parsed resume against a parsed job.

        Returns a normalized dictionary containing both matching
        information and an ATS-style target-job report.
        """

        resume_skills = self._normalize_skills(
            getattr(resume, "skills", [])
        )

        job_skills = self._normalize_skills(
            getattr(job, "skills", [])
        )

        matched_skills = sorted(
            resume_skills.intersection(job_skills)
        )

        missing_skills = sorted(
            job_skills.difference(resume_skills)
        )

        skill_score = self._calculate_skill_score(
            resume_skills,
            job_skills,
        )

        keyword_score = self._calculate_keyword_score(
            resume,
            job,
        )

        experience_score = self._calculate_experience_score(
            resume,
            job,
        )

        education_score = self._calculate_education_score(
            resume,
            job,
        )

        project_score = self._calculate_project_score(
            resume,
            job,
        )

        overall_score = self._calculate_overall_score(
            skill_score=skill_score,
            keyword_score=keyword_score,
            experience_score=experience_score,
            education_score=education_score,
            project_score=project_score,
        )

        skill_coverage = (
            round(
                len(matched_skills)
                / len(job_skills)
                * 100
            )
            if job_skills
            else 0
        )

        result = {
            "job_title": self._safe_string(
                getattr(job, "title", "")
            ),

            "company": self._safe_string(
                getattr(job, "company", "")
            ),

            "match_score": overall_score,

            "skill_coverage": skill_coverage,

            "breakdown": {
                "skills": skill_score,
                "keywords": keyword_score,
                "experience": experience_score,
                "education": education_score,
                "project_relevance": project_score,
            },

            "matched_skills": matched_skills,

            "missing_skills": missing_skills,

            "skills_to_improve": missing_skills,
        }

        logger.info(
            "Job matching completed. Overall=%s Skill=%s Keyword=%s "
            "Experience=%s Education=%s Project=%s",
            overall_score,
            skill_score,
            keyword_score,
            experience_score,
            education_score,
            project_score,
        )

        return result

    def compare(self, resume, job) -> Dict[str, Any]:
        """
        Compatibility wrapper used by AnalysisPipeline.

        The original pipeline expected:

            {
                "match_result": ...,
                "ats_report": ...
            }

        This method now provides exactly that structure while
        keeping `match()` available for existing code.
        """

        matching = self.match(
            resume,
            job,
        )

        match_result = MatchResult.from_dict(
            matching
        )

        ats_report = self._build_target_job_ats_report(
            resume=resume,
            job=job,
            matching=matching,
        )

        return {
            "match_result": match_result,
            "ats_report": ats_report,
        }

    # =========================================================
    # OVERALL SCORE
    # =========================================================

    @staticmethod
    def _calculate_overall_score(
        skill_score: float,
        keyword_score: float,
        experience_score: float,
        education_score: float,
        project_score: float,
    ) -> int:
        """
        Calculate weighted target-job match score.
        """

        weights = {
            "skills": 0.40,
            "keywords": 0.20,
            "experience": 0.15,
            "education": 0.10,
            "project_relevance": 0.15,
        }

        try:
            configured = JOB_MATCH_WEIGHTS

            if isinstance(configured, dict):
                weights = {
                    "skills": float(
                        configured.get(
                            "skills",
                            weights["skills"] * 100,
                        )
                    ) / 100,

                    "keywords": float(
                        configured.get(
                            "keywords",
                            weights["keywords"] * 100,
                        )
                    ) / 100,

                    "experience": float(
                        configured.get(
                            "experience",
                            weights["experience"] * 100,
                        )
                    ) / 100,

                    "education": float(
                        configured.get(
                            "education",
                            weights["education"] * 100,
                        )
                    ) / 100,

                    "project_relevance": float(
                        configured.get(
                            "project_relevance",
                            weights["project_relevance"] * 100,
                        )
                    ) / 100,
                }

                total_weight = sum(
                    weights.values()
                )

                if total_weight > 0:
                    weights = {
                        key: value / total_weight
                        for key, value in weights.items()
                    }

        except Exception:
            logger.exception(
                "Could not load JOB_MATCH_WEIGHTS. "
                "Using safe default weights."
            )

        score = (
            skill_score * weights["skills"]
            + keyword_score * weights["keywords"]
            + experience_score * weights["experience"]
            + education_score * weights["education"]
            + project_score * weights["project_relevance"]
        )

        return max(
            0,
            min(
                100,
                round(score),
            ),
        )

    # =========================================================
    # SKILL MATCH
    # =========================================================

    @classmethod
    def _calculate_skill_score(
        cls,
        resume_skills: Set[str],
        job_skills: Set[str],
    ) -> int:
        """
        Calculate percentage of required job skills present
        in the resume.
        """

        if not job_skills:
            return 0

        matched = resume_skills.intersection(
            job_skills
        )

        return max(
            0,
            min(
                100,
                round(
                    len(matched)
                    / len(job_skills)
                    * 100
                ),
            ),
        )

    # =========================================================
    # KEYWORD MATCH
    # =========================================================

    def _calculate_keyword_score(
        self,
        resume,
        job,
    ) -> int:
        """
        Compare job keywords against the resume text.

        If explicit job keywords are unavailable, useful terms
        are extracted from the job description.
        """

        resume_text = self._resume_to_text(
            resume
        ).lower()

        job_keywords = self._get_job_keywords(
            job
        )

        if not job_keywords:
            return 0

        matched = 0

        for keyword in job_keywords:

            normalized = self._normalize_phrase(
                keyword
            )

            if not normalized:
                continue

            if normalized in resume_text:
                matched += 1

        if not job_keywords:
            return 0

        return max(
            0,
            min(
                100,
                round(
                    matched
                    / len(job_keywords)
                    * 100
                ),
            ),
        )

    # =========================================================
    # EXPERIENCE MATCH
    # =========================================================

    def _calculate_experience_score(
        self,
        resume,
        job,
    ) -> int:
        """
        Estimate experience compatibility.

        This deliberately avoids giving 100 merely because a
        resume contains any experience.
        """

        required = self._safe_string(
            getattr(
                job,
                "experience",
                "",
            )
        ).strip().lower()

        resume_experience = getattr(
            resume,
            "experience",
            None,
        )

        resume_text = self._safe_string(
            resume_experience
        ).lower()

        if not required:
            return 70

        required_years = self._extract_years(
            required
        )

        resume_years = self._extract_years(
            resume_text
        )

        if required_years is not None:

            if resume_years is None:

                if self._looks_like_fresher(
                    resume_text
                ):
                    return 80

                if resume_text:
                    return 70

                return 40

            if resume_years >= required_years:
                return 100

            if resume_years >= required_years * 0.75:
                return 85

            if resume_years >= required_years * 0.5:
                return 70

            if resume_years > 0:
                return 55

            return 40

        if not resume_text:
            return 40

        required_terms = [
            "senior",
            "lead",
            "manager",
            "mid-level",
            "mid level",
            "experienced",
        ]

        if any(
            term in required
            for term in required_terms
        ):
            if any(
                term in resume_text
                for term in [
                    "senior",
                    "lead",
                    "manager",
                    "years",
                    "year",
                ]
            ):
                return 80

            return 50

        return 75

    # =========================================================
    # EDUCATION MATCH
    # =========================================================

    def _calculate_education_score(
        self,
        resume,
        job,
    ) -> int:
        """
        Compare education requirement with resume education.
        """

        required = self._safe_string(
            getattr(
                job,
                "education",
                "",
            )
        ).lower().strip()

        education = getattr(
            resume,
            "education",
            [],
        )

        resume_text = self._safe_string(
            education
        ).lower()

        if not required:
            return 70

        if not resume_text:
            return 30

        required_terms = self._extract_important_terms(
            required
        )

        if not required_terms:
            return 70

        matched = sum(
            1
            for term in required_terms
            if term in resume_text
        )

        coverage = (
            matched
            / len(required_terms)
        )

        if coverage >= 0.75:
            return 100

        if coverage >= 0.5:
            return 85

        if coverage > 0:
            return 70

        return 50

    # =========================================================
    # PROJECT RELEVANCE
    # =========================================================

    def _calculate_project_score(
        self,
        resume,
        job,
    ) -> int:
        """
        Estimate project relevance by comparing job skills,
        keywords and resume project text.
        """

        projects = getattr(
            resume,
            "projects",
            [],
        )

        project_text = self._safe_string(
            projects
        ).lower()

        if not project_text.strip():
            return 30

        job_skills = self._normalize_skills(
            getattr(
                job,
                "skills",
                [],
            )
        )

        if not job_skills:
            return 60

        matched = 0

        for skill in job_skills:

            if skill in project_text:
                matched += 1

        if matched == 0:
            return 35

        score = round(
            matched
            / len(job_skills)
            * 100
        )

        return max(
            35,
            min(
                100,
                score,
            ),
        )

    # =========================================================
    # TARGET ATS REPORT
    # =========================================================

    def _build_target_job_ats_report(
        self,
        resume,
        job,
        matching: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build the ATS report for a specific target job.

        This is NOT the generic resume completeness score.

        It reflects:

            - required skills
            - keywords
            - experience
            - education
            - project relevance
        """

        breakdown = matching.get(
            "breakdown",
            {},
        )

        score = matching.get(
            "match_score",
            0,
        )

        matched_skills = matching.get(
            "matched_skills",
            [],
        )

        missing_skills = matching.get(
            "missing_skills",
            [],
        )

        keyword_score = breakdown.get(
            "keywords",
            0,
        )

        skill_score = breakdown.get(
            "skills",
            0,
        )

        experience_score = breakdown.get(
            "experience",
            0,
        )

        education_score = breakdown.get(
            "education",
            0,
        )

        project_score = breakdown.get(
            "project_relevance",
            0,
        )

        strengths: List[str] = []
        weaknesses: List[str] = []
        improvements: List[str] = []

        if skill_score >= 80:
            strengths.append(
                "Most required technical skills are present."
            )
        elif skill_score >= 50:
            strengths.append(
                "Several required technical skills are present."
            )
        else:
            weaknesses.append(
                "Important technical skills are missing."
            )

        if keyword_score >= 75:
            strengths.append(
                "Resume contains many relevant job keywords."
            )
        elif keyword_score < 50:
            weaknesses.append(
                "Resume is missing important ATS keywords."
            )

        if experience_score >= 80:
            strengths.append(
                "Experience appears compatible with the target role."
            )
        elif experience_score < 60:
            weaknesses.append(
                "Experience may not fully satisfy the job requirement."
            )

        if education_score >= 80:
            strengths.append(
                "Education appears compatible with the job requirement."
            )
        elif education_score < 60:
            weaknesses.append(
                "Education does not strongly match the job requirement."
            )

        if project_score >= 75:
            strengths.append(
                "Projects show good relevance to the target role."
            )
        elif project_score < 50:
            weaknesses.append(
                "Projects do not strongly demonstrate the required skills."
            )

        if missing_skills:
            improvements.append(
                "Add or strengthen relevant skills only if you genuinely possess them: "
                + ", ".join(missing_skills[:8])
                + "."
            )

        if keyword_score < 75:
            improvements.append(
                "Use relevant job-specific keywords naturally in your resume "
                "where they accurately describe your experience."
            )

        if project_score < 70:
            improvements.append(
                "Highlight projects that demonstrate skills relevant to the target role."
            )

        if not improvements:
            improvements.append(
                "Tailor the resume further to the exact target job description."
            )

        score = max(
            0,
            min(
                100,
                round(float(score), 2),
            ),
        )

        if score >= 90:
            grade = "A+"
        elif score >= 85:
            grade = "A"
        elif score >= 75:
            grade = "B"
        elif score >= 65:
            grade = "C"
        elif score >= 50:
            grade = "D"
        else:
            grade = "F"

        return {
            "score": score,
            "grade": grade,

            "strengths": strengths,

            "weaknesses": weaknesses,

            "improvements": improvements,

            "matched_skills": matched_skills,

            "missing_skills": missing_skills,

            "score_breakdown": {
                "skills": skill_score,
                "keywords": keyword_score,
                "experience": experience_score,
                "education": education_score,
                "project_relevance": project_score,
            },

            "job_title": self._safe_string(
                getattr(
                    job,
                    "title",
                    "",
                )
            ),

            "company": self._safe_string(
                getattr(
                    job,
                    "company",
                    "",
                )
            ),
        }

    # =========================================================
    # SKILL NORMALIZATION
    # =========================================================

    @classmethod
    def _normalize_skills(
        cls,
        skills: Any,
    ) -> Set[str]:
        """
        Normalize skills safely.

        Supports:

            "Python"

            ["Python", "FastAPI"]

            {"name": "Python"}

            [{"name": "Python"}]

        This prevents AI-generated dictionary values from
        breaking deterministic matching.
        """

        result: Set[str] = set()

        if skills is None:
            return result

        if isinstance(
            skills,
            (str, bytes),
        ):
            skills = [
                skills
            ]

        elif isinstance(
            skills,
            dict,
        ):
            skills = [
                skills
            ]

        try:
            iterator = iter(
                skills
            )
        except TypeError:
            iterator = iter(
                [skills]
            )

        for skill in iterator:

            value = cls._extract_skill_value(
                skill
            )

            value = cls._normalize_phrase(
                value
            )

            if value:
                result.add(value)

        return result

    @staticmethod
    def _extract_skill_value(
        skill: Any,
    ) -> str:
        if skill is None:
            return ""

        if isinstance(
            skill,
            str,
        ):
            return skill

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
                    )

            return ""

        return str(
            skill
        )

    # =========================================================
    # JOB KEYWORDS
    # =========================================================

    def _get_job_keywords(
        self,
        job,
    ) -> List[str]:
        keywords = getattr(
            job,
            "keywords",
            None,
        )

        if keywords:

            normalized = []

            if isinstance(
                keywords,
                dict,
            ):
                keywords = (
                    keywords.keys()
                )

            elif isinstance(
                keywords,
                str,
            ):
                keywords = re.split(
                    r"[,;\n|]",
                    keywords,
                )

            for keyword in keywords:

                value = self._extract_skill_value(
                    keyword
                )

                value = self._normalize_phrase(
                    value
                )

                if (
                    value
                    and value not in normalized
                ):
                    normalized.append(
                        value
                    )

            if normalized:
                return normalized

        job_text = self._job_to_text(
            job
        )

        return self._extract_important_terms(
            job_text
        )[:20]

    # =========================================================
    # TEXT HELPERS
    # =========================================================

    @classmethod
    def _resume_to_text(
        cls,
        resume,
    ) -> str:

        parts = []

        for attribute in (
            "name",
            "summary",
            "skills",
            "experience",
            "education",
            "projects",
            "certifications",
            "career_profile",
        ):

            value = getattr(
                resume,
                attribute,
                None,
            )

            if value is not None:

                if hasattr(
                    value,
                    "to_dict",
                ):
                    try:
                        value = value.to_dict()
                    except Exception:
                        pass

                parts.append(
                    cls._safe_string(
                        value
                    )
                )

        return "\n".join(
            parts
        )

    @classmethod
    def _job_to_text(
        cls,
        job,
    ) -> str:

        parts = []

        for attribute in (
            "title",
            "company",
            "summary",
            "description",
            "skills",
            "keywords",
            "responsibilities",
            "experience",
            "education",
        ):

            value = getattr(
                job,
                attribute,
                None,
            )

            if value is not None:

                parts.append(
                    cls._safe_string(
                        value
                    )
                )

        return "\n".join(
            parts
        )

    @staticmethod
    def _safe_string(
        value: Any,
    ) -> str:

        if value is None:
            return ""

        if isinstance(
            value,
            dict,
        ):

            return " ".join(
                str(item)
                for item in value.values()
                if item is not None
            )

        if isinstance(
            value,
            (list, tuple, set),
        ):

            return " ".join(
                str(item)
                for item in value
                if item is not None
            )

        return str(
            value
        )

    @staticmethod
    def _normalize_phrase(
        value: Any,
    ) -> str:

        if value is None:
            return ""

        value = str(
            value
        ).strip().lower()

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value

    @staticmethod
    def _extract_years(
        text: str,
    ):
        if not text:
            return None

        patterns = [
            r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
            r"(\d+(?:\.\d+)?)\s*[-to]+\s*\d+\s*(?:years?|yrs?)",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:

                try:
                    return float(
                        match.group(1)
                    )
                except (
                    ValueError,
                    TypeError,
                ):
                    return None

        return None

    @staticmethod
    def _looks_like_fresher(
        text: str,
    ) -> bool:

        if not text:
            return False

        fresher_terms = (
            "fresher",
            "entry level",
            "entry-level",
            "intern",
            "internship",
            "student",
            "0 years",
            "0-1 years",
            "0 - 1 years",
            "0 to 1 years",
        )

        return any(
            term in text
            for term in fresher_terms
        )

    @staticmethod
    def _extract_important_terms(
        text: str,
    ) -> List[str]:
        """
        Extract useful keyword-like phrases while ignoring
        common English stop words.
        """

        if not text:
            return []

        text = str(
            text
        ).lower()

        phrases = re.findall(
            r"[a-zA-Z][a-zA-Z0-9+#.\-/]{1,30}",
            text,
        )

        stop_words = {
            "the",
            "and",
            "for",
            "with",
            "that",
            "this",
            "from",
            "your",
            "you",
            "are",
            "our",
            "will",
            "have",
            "has",
            "job",
            "role",
            "work",
            "working",
            "years",
            "year",
            "experience",
            "required",
            "requirements",
            "responsibilities",
            "candidate",
            "company",
            "team",
            "using",
            "ability",
            "strong",
            "good",
            "knowledge",
            "skills",
            "skill",
            "must",
            "should",
            "preferred",
            "including",
            "such",
            "into",
            "their",
            "they",
            "our",
            "about",
            "than",
            "then",
            "also",
            "not",
            "all",
            "any",
            "can",
            "may",
            "who",
            "what",
            "how",
            "where",
            "when",
            "why",
            "to",
            "of",
            "in",
            "on",
            "at",
            "by",
            "as",
            "an",
            "a",
            "is",
            "be",
            "or",
            "it",
            "we",
            "he",
            "she",
            "i",
        }

        result = []

        for phrase in phrases:

            phrase = phrase.strip(
                ".,;:()[]{}"
            )

            if (
                len(phrase) < 2
                or phrase in stop_words
            ):
                continue

            if phrase not in result:
                result.append(
                    phrase
                )

        return result


# =============================================================
# MATCH RESULT MODEL
# =============================================================

class MatchResult:
    """
    Lightweight result object used by AnalysisPipeline.

    It intentionally supports `to_dict()` so the pipeline can
    serialize the target-job result without changing the rest
    of the application.
    """

    def __init__(
        self,
        job_title: str = "",
        company: str = "",
        overall_score: int = 0,
        skill_coverage: int = 0,
        breakdown: Dict[str, Any] | None = None,
        matched_skills: List[str] | None = None,
        missing_skills: List[str] | None = None,
        skills_to_improve: List[str] | None = None,
    ):

        self.job_title = job_title
        self.company = company
        self.overall_score = overall_score
        self.skill_coverage = skill_coverage
        self.breakdown = breakdown or {}
        self.matched_skills = matched_skills or []
        self.missing_skills = missing_skills or []
        self.skills_to_improve = (
            skills_to_improve
            if skills_to_improve is not None
            else list(self.missing_skills)
        )

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ):

        return cls(
            job_title=data.get(
                "job_title",
                "",
            ),
            company=data.get(
                "company",
                "",
            ),
            overall_score=data.get(
                "match_score",
                data.get(
                    "overall_score",
                    0,
                ),
            ),
            skill_coverage=data.get(
                "skill_coverage",
                0,
            ),
            breakdown=data.get(
                "breakdown",
                {},
            ),
            matched_skills=data.get(
                "matched_skills",
                [],
            ),
            missing_skills=data.get(
                "missing_skills",
                [],
            ),
            skills_to_improve=data.get(
                "skills_to_improve",
                [],
            ),
        )

    def to_dict(self) -> Dict[str, Any]:

        return {
            "job_title": self.job_title,
            "company": self.company,
            "overall_score": self.overall_score,
            "match_score": self.overall_score,
            "skill_coverage": self.skill_coverage,
            "breakdown": self.breakdown,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "skills_to_improve": self.skills_to_improve,
        }
