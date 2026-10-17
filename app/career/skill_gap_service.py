from typing import Dict, List, Optional, Set

from app.models.skill_gap import SkillGapResult, SkillGap


class SkillGapService:
    """
    Deterministic Skill Gap Analysis Service.

    Compares resume skills against target/job skills and produces
    a structured SkillGapResult.

    AI can be added later for intelligent prioritization, but the
    basic comparison remains deterministic and reliable.
    """

    SKILL_ALIASES = {
        "python programming": "python",
        "python programming language": "python",
        "structured query language": "sql",
        "mysql database": "mysql",
        "git/github": "git",
        "github": "git",
        "amazon web services": "aws",
        "amazon web service": "aws",
        "k8s": "kubernetes",
        "restful api": "rest api",
        "restful apis": "rest api",
        "rest api development": "rest api",
        "rest apis": "rest api",
        "ci cd": "ci/cd",
        "ci/cd pipeline": "ci/cd",
        "continuous integration": "ci/cd",
        "continuous integration and deployment": "ci/cd",
    }

    def __init__(self):
        pass

    # ---------------------------------------------------------
    # NORMALIZATION
    # ---------------------------------------------------------

    @classmethod
    def normalize_skill(cls, skill: str) -> str:
        """
        Normalize a single skill.
        """

        if not skill:
            return ""

        value = skill.strip().lower()

        # Remove unnecessary surrounding punctuation
        value = value.strip(".,;:()[]{}")

        # Normalize multiple spaces
        value = " ".join(value.split())

        return cls.SKILL_ALIASES.get(value, value)

    @classmethod
    def normalize_skills(cls, skills: List[str]) -> List[str]:
        """
        Normalize skills and remove duplicates.
        """

        normalized: List[str] = []

        for skill in skills or []:
            value = cls.normalize_skill(skill)

            if value and value not in normalized:
                normalized.append(value)

        return normalized

    # ---------------------------------------------------------
    # PARTIAL MATCHING
    # ---------------------------------------------------------

    @staticmethod
    def _is_partial_match(
        resume_skill: str,
        target_skill: str,
    ) -> bool:
        """
        Detect simple partial/related skill matches.

        This intentionally remains conservative to avoid
        falsely claiming that a candidate possesses a skill.
        """

        if resume_skill == target_skill:
            return False

        resume_words = set(resume_skill.split())
        target_words = set(target_skill.split())

        if not resume_words or not target_words:
            return False

        # Example:
        # "rest api" vs "rest api development"
        common_words = resume_words.intersection(target_words)

        if len(common_words) >= 2:
            return True

        return False

    # ---------------------------------------------------------
    # COMPARISON
    # ---------------------------------------------------------

    def compare_skills(
        self,
        resume_skills: List[str],
        target_skills: List[str],
    ) -> Dict[str, List[str]]:

        resume = self.normalize_skills(resume_skills)
        target = self.normalize_skills(target_skills)

        resume_set: Set[str] = set(resume)
        target_set: Set[str] = set(target)

        matched = sorted(
            resume_set.intersection(target_set)
        )

        missing = sorted(
            target_set.difference(resume_set)
        )

        partial = []

        # Remove skills that are already matched
        unmatched_resume = resume_set.difference(matched)

        for target_skill in missing[:]:

            for resume_skill in unmatched_resume:

                if self._is_partial_match(
                    resume_skill,
                    target_skill,
                ):
                    partial.append(target_skill)
                    break

        # A partial match should not also remain in missing
        missing = [
            skill
            for skill in missing
            if skill not in partial
        ]

        additional = sorted(
            resume_set.difference(target_set)
        )

        return {
            "matched": matched,
            "partial": sorted(set(partial)),
            "missing": missing,
            "additional": additional,
        }

    # ---------------------------------------------------------
    # MAIN ANALYSIS
    # ---------------------------------------------------------

    def analyze(
        self,
        resume_skills: List[str],
        target_skills: List[str],
        target_role: Optional[str] = None,
    ) -> SkillGapResult:

        comparison = self.compare_skills(
            resume_skills=resume_skills,
            target_skills=target_skills,
        )

        missing_skills = comparison["missing"]

        # -----------------------------------------------------
        # PRIORITY
        # -----------------------------------------------------

        priority_gaps = []

        for skill in missing_skills:

            priority = "medium"

            # Core technologies are generally high-value gaps.
            high_priority_keywords = {
                "python",
                "java",
                "javascript",
                "typescript",
                "sql",
                "aws",
                "azure",
                "gcp",
                "docker",
                "kubernetes",
                "machine learning",
                "data science",
                "cyber security",
                "cybersecurity",
            }

            if skill in high_priority_keywords:
                priority = "high"

            priority_gaps.append(
                SkillGap(
                    skill=skill,
                    priority=priority,
                    reason=(
                        f"{skill} is required for the target role "
                        "but is not listed in the resume."
                    ),
                )
            )

        # -----------------------------------------------------
        # RECOMMENDED ACTIONS
        # -----------------------------------------------------

        actions = []

        for skill in missing_skills:

            actions.append(
                f"Develop practical knowledge of {skill}."
            )

        # -----------------------------------------------------
        # RESULT
        # -----------------------------------------------------

        return SkillGapResult(
            target_role=target_role,

            matched_skills=comparison["matched"],

            partial_skills=comparison["partial"],

            missing_skills=comparison["missing"],

            priority_gaps=priority_gaps,

            recommended_actions=actions,
        )

    # ---------------------------------------------------------
    # SCORE
    # ---------------------------------------------------------

    def calculate_match_score(
        self,
        resume_skills: List[str],
        target_skills: List[str],
    ) -> float:

        comparison = self.compare_skills(
            resume_skills,
            target_skills,
        )

        target_count = len(
            self.normalize_skills(target_skills)
        )

        if target_count == 0:
            return 100.0

        matched_count = len(
            comparison["matched"]
        )

        return round(
            (matched_count / target_count) * 100,
            2,
        )