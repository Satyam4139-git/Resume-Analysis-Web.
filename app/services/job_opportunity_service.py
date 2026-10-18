"""
Job Opportunity Service
=======================

Adapter between AnalysisPipeline and JobSearchService.

Responsibilities:

1. Extract resume skills.
2. Search real jobs.
3. Convert job objects.
4. Calculate resume/job skill matching.
5. Calculate a realistic match score.
6. Identify matched skills.
7. Identify missing skills.
8. Remove duplicate jobs.
9. Return limited real opportunities.
"""

from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from app.core.logger import logger
from app.jobs.job_search_service import JobSearchService


# How many "Suitable Job Openings" to show after an analysis.
DEFAULT_LIMIT = max(1, int(os.getenv("SUITABLE_JOBS_LIMIT", "65")))

# Jobs fetched per search term (a resume produces up to 3 terms).
PER_TERM_LIMIT = 40


class JobOpportunityService:

    def __init__(self):

        self.job_search_service = JobSearchService()

        logger.info(
            "JobOpportunityService initialized."
        )

    # ==========================================================
    # PUBLIC SEARCH
    # ==========================================================

    def search_jobs(
        self,
        resume,
        limit: int = DEFAULT_LIMIT,
    ) -> List[Dict[str, Any]]:
        """
        Real job postings that fit the resume AND the candidate's
        experience level (a fresher is not shown senior jobs).

        Uses the shared JobBoardService: one request per search term, run
        in parallel, with caching and 8 second timeouts.
        """

        if resume is None:

            raise ValueError(
                "Resume cannot be None."
            )

        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = DEFAULT_LIMIT

        if limit <= 0:
            return []

        from app.jobs.job_board import LEVEL_NAMES as BOARD_LEVELS
        from app.jobs.job_board import get_job_board
        from app.utils.seniority import get_level

        board = get_job_board()

        if not board.configured:

            logger.warning(
                "Job search skipped: no job provider configured."
            )

            return []

        level, years = get_level(resume)

        level_name = BOARD_LEVELS.get(level, "")

        terms = self._build_search_terms(resume)[:3]

        if not terms:

            return []

        logger.info(
            "Searching jobs: terms=%s level=%s",
            terms,
            level_name or "any",
        )

        def run(term, wanted_level):
            try:
                return board.search(
                    q=term,
                    level=wanted_level,
                    limit=PER_TERM_LIMIT,
                ).get("jobs", [])
            except Exception as error:
                logger.warning("Job search failed for '%s': %s", term, error)
                return []

        def gather(wanted_level):
            with ThreadPoolExecutor(max_workers=len(terms)) as pool:
                batches = list(
                    pool.map(lambda t: run(t, wanted_level), terms)
                )
            return [item for batch in batches for item in batch]

        items = gather(level_name)

        # Too few exact-level jobs (common for freshers)? Search again
        # without the level filter and keep every job that is not clearly
        # too senior / too junior; slight stretch roles rank lower.
        distinct = {i.get("url") for i in items if i.get("url")}

        if level_name and len(distinct) < limit:
            items += gather("")

        from app.utils.seniority import level_fit

        opportunities = []
        seen = set()

        for item in items:

            url = item.get("url", "")

            if not url or url in seen:
                continue

            fit = level_fit(
                level,
                years,
                item.get("title", ""),
                item.get("description", ""),
            )

            if fit["exclude"]:
                continue

            seen.add(url)

            job = {
                "company": item.get("company", ""),
                "title": item.get("title", ""),
                "location": item.get("location", ""),
                "description": item.get("description", ""),
                "job_url": url,
                "source": item.get("source", ""),
                "salary_min": item.get("salary_min"),
                "salary_max": item.get("salary_max"),
                "level": item.get("level", ""),
                "remote": item.get("remote", False),
            }

            if fit["note"]:
                job["level_fit"] = fit["note"]

            job.update(
                self._calculate_match(
                    resume,
                    job,
                )
            )

            job["_rank"] = (
                float(job.get("match_score", 0) or 0)
                * fit["multiplier"]
            )

            opportunities.append(job)

        # Pick the final list by taking turns between sources (best first
        # within each), so Adzuna AND Jooble are both represented; then
        # show the chosen jobs best-match first.
        by_source: Dict[str, List[Dict[str, Any]]] = {}

        for item in sorted(
            opportunities,
            key=lambda item: item.get("_rank", 0),
            reverse=True,
        ):
            by_source.setdefault(item.get("source", ""), []).append(item)

        queues = list(by_source.values())
        chosen: List[Dict[str, Any]] = []

        while len(chosen) < limit and any(queues):
            for queue in queues:
                if queue and len(chosen) < limit:
                    chosen.append(queue.pop(0))

        chosen.sort(
            key=lambda item: item.get("_rank", 0),
            reverse=True,
        )

        for item in chosen:
            item.pop("_rank", None)

        return chosen

    # ==========================================================
    # BUILD SEARCH TERMS
    # ==========================================================

    @staticmethod
    def _build_search_terms(
        resume,
    ) -> List[str]:
        """
        Role-based search terms ("Backend Developer", "Data Analyst"), not
        raw skill names: skill names alone return the same jobs for
        everybody. Experience level is applied separately as a filter.
        """

        from app.career.opportunity_engine import OpportunityEngine

        terms: List[str] = []

        try:
            for role in OpportunityEngine.recommend(resume, limit=3):
                base = role.get("base_role")
                if base and base not in terms:
                    terms.append(base)
        except Exception:
            logger.exception("Could not derive search terms from roles.")

        profile = getattr(resume, "career_profile", None)
        profile_role = (getattr(profile, "role", "") or "").strip()

        if profile_role and profile_role not in terms:
            terms.insert(0, profile_role)

        if not terms:

            for skill in getattr(resume, "skills", []) or []:

                if isinstance(skill, str) and skill.strip():
                    terms.append(f"{skill.strip()} developer")
                    break

        return terms[:3]

    # ==========================================================
    # NORMALIZE SKILL
    # ==========================================================

    @staticmethod
    def _normalize_skill(
        skill: Any,
    ) -> str:

        if isinstance(
            skill,
            dict,
        ):

            skill = (
                skill.get("name")
                or skill.get("skill")
                or skill.get("title")
                or skill.get("value")
                or ""
            )

        skill = str(
            skill or ""
        ).lower().strip()

        skill = skill.replace(
            "&",
            " and ",
        )

        skill = re.sub(
            r"[^a-z0-9+#.\- ]+",
            " ",
            skill,
        )

        skill = re.sub(
            r"\s+",
            " ",
            skill,
        )

        return skill.strip()

    # ==========================================================
    # RESUME SKILLS
    # ==========================================================

    @classmethod
    def _resume_skills(
        cls,
        resume,
    ) -> List[str]:

        skills = getattr(
            resume,
            "skills",
            [],
        ) or []

        result = []

        for skill in skills:

            normalized = cls._normalize_skill(
                skill
            )

            if normalized:
                result.append(
                    normalized
                )

        return list(
            dict.fromkeys(
                result
            )
        )

    # ==========================================================
    # EXTRACT SKILLS FROM JOB
    # ==========================================================

    @classmethod
    def _extract_job_skills(
        cls,
        job: Dict[str, Any],
    ) -> List[str]:

        explicit = []

        for key in [
            "skills",
            "required_skills",
            "matched_skills",
        ]:

            value = job.get(
                key,
                [],
            )

            if isinstance(
                value,
                list,
            ):
                explicit.extend(
                    value
                )

            elif isinstance(
                value,
                str,
            ):
                explicit.extend(
                    re.split(
                        r"[,|;/]",
                        value,
                    )
                )

        # ------------------------------------------------------
        # Extract known technologies from description.
        # ------------------------------------------------------

        description = str(
            job.get(
                "description",
                "",
            )
            or ""
        )

        title = str(
            job.get(
                "title",
                "",
            )
            or ""
        )

        source_text = (
            title
            + " "
            + description
        ).lower()

        known_skills = [
            "python",
            "java",
            "c++",
            "c#",
            "javascript",
            "typescript",
            "sql",
            "mysql",
            "postgresql",
            "mongodb",
            "oracle",
            "fastapi",
            "django",
            "flask",
            "react",
            "angular",
            "node.js",
            "nodejs",
            "rest api",
            "rest apis",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "git",
            "github",
            "linux",
            "windows",
            "power bi",
            "tableau",
            "excel",
            "pandas",
            "numpy",
            "pytorch",
            "tensorflow",
            "scikit-learn",
            "machine learning",
            "deep learning",
            "nlp",
            "spark",
            "pyspark",
            "databricks",
            "hadoop",
            "etl",
            "data analysis",
            "data analytics",
            "cybersecurity",
            "cyber security",
            "wireshark",
            "burp suite",
            "cisco",
            "powershell",
            "bash",
        ]

        for skill in known_skills:

            if skill in source_text:
                explicit.append(
                    skill
                )

        normalized = []

        for skill in explicit:

            value = cls._normalize_skill(
                skill
            )

            if value:
                normalized.append(
                    value
                )

        return list(
            dict.fromkeys(
                normalized
            )
        )

    # ==========================================================
    # MATCH CALCULATION
    # ==========================================================

    @classmethod
    def _calculate_match(
        cls,
        resume,
        job: Dict[str, Any],
    ) -> Dict[str, Any]:

        resume_skills = cls._resume_skills(
            resume
        )

        job_skills = cls._extract_job_skills(
            job
        )

        # ------------------------------------------------------
        # Exact / phrase matching
        # ------------------------------------------------------

        matched = []
        missing = []

        for job_skill in job_skills:

            found = False

            for resume_skill in resume_skills:

                if (
                    job_skill == resume_skill
                    or job_skill in resume_skill
                    or resume_skill in job_skill
                ):

                    found = True
                    break

            if found:
                matched.append(
                    job_skill
                )
            else:
                missing.append(
                    job_skill
                )

        # ------------------------------------------------------
        # If job has no detected skills, calculate a conservative
        # title/description relevance score rather than 100%.
        # ------------------------------------------------------

        if not job_skills:

            title = cls._normalize_skill(
                job.get(
                    "title",
                    "",
                )
            )

            relevance_hits = 0

            for resume_skill in resume_skills:

                if resume_skill in title:
                    relevance_hits += 1

            if resume_skills:

                relevance_score = (
                    relevance_hits
                    / len(resume_skills)
                ) * 100

            else:
                relevance_score = 0

            match_score = min(
                60,
                round(
                    relevance_score,
                    2,
                ),
            )

            return {
                "match_score": match_score,
                "matched_skills": [],
                "missing_skills": [],
                "why_suitable": [
                    (
                        "Job-specific skill requirements "
                        "could not be extracted."
                    )
                ],
            }

        # ------------------------------------------------------
        # Skill score
        # ------------------------------------------------------

        skill_score = (
            len(matched)
            / len(job_skills)
        ) * 100

        # ------------------------------------------------------
        # Resume keyword relevance
        # ------------------------------------------------------

        description = str(
            job.get(
                "description",
                "",
            )
            or ""
        ).lower()

        keyword_hits = 0

        for resume_skill in resume_skills:

            if resume_skill in description:
                keyword_hits += 1

        keyword_score = (
            (
                keyword_hits
                / len(resume_skills)
            )
            * 100
            if resume_skills
            else 0
        )

        # ------------------------------------------------------
        # Final weighted score
        #
        # Skills are given the largest weight.
        # Keywords provide additional relevance.
        # ------------------------------------------------------

        match_score = (
            skill_score * 0.75
            + keyword_score * 0.25
        )

        match_score = max(
            0,
            min(
                100,
                round(
                    match_score,
                    2,
                ),
            ),
        )

        why_suitable = []

        if matched:

            why_suitable.append(
                "Matching skills: "
                + ", ".join(
                    matched[:8]
                )
            )

        if missing:

            why_suitable.append(
                "Skills to develop: "
                + ", ".join(
                    missing[:8]
                )
            )

        if keyword_score >= 50:

            why_suitable.append(
                "Your resume contains several "
                "keywords relevant to this job."
            )

        return {
            "match_score": match_score,
            "matched_skills": matched,
            "missing_skills": missing,
            "why_suitable": why_suitable,
        }

    # ==========================================================
    # CONVERT OPPORTUNITY
    # ==========================================================

    @staticmethod
    def _convert_opportunity(
        opportunity,
    ) -> Dict[str, Any]:

        # ------------------------------------------------------
        # Object
        # ------------------------------------------------------

        if hasattr(
            opportunity,
            "to_dict",
        ):

            try:

                data = opportunity.to_dict()

            except Exception as error:

                logger.exception(
                    "Failed to convert job opportunity.",
                )

                return {}

        # ------------------------------------------------------
        # Dictionary
        # ------------------------------------------------------

        elif isinstance(
            opportunity,
            dict,
        ):

            data = dict(
                opportunity
            )

        else:

            logger.warning(
                "Unsupported opportunity type: %s",
                type(opportunity),
            )

            return {}

        # ------------------------------------------------------
        # URL
        # ------------------------------------------------------

        job_url = (
            data.get(
                "job_url"
            )
            or data.get(
                "url"
            )
            or ""
        )

        # ------------------------------------------------------
        # Why suitable
        # ------------------------------------------------------

        why_suitable = data.get(
            "why_suitable",
            [],
        )

        if isinstance(
            why_suitable,
            str,
        ):

            why_suitable = [
                why_suitable
            ]

        elif not isinstance(
            why_suitable,
            list,
        ):

            why_suitable = []

        # ------------------------------------------------------
        # Skills
        # ------------------------------------------------------

        matched_skills = data.get(
            "matched_skills",
            [],
        )

        if not isinstance(
            matched_skills,
            list,
        ):
            matched_skills = []

        missing_skills = data.get(
            "missing_skills",
            [],
        )

        if not isinstance(
            missing_skills,
            list,
        ):
            missing_skills = []

        # ------------------------------------------------------
        # Final normalized object
        # ------------------------------------------------------

        try:

            existing_match_score = float(
                data.get(
                    "match_score",
                    0,
                )
                or 0
            )

        except (
            TypeError,
            ValueError,
        ):

            existing_match_score = 0

        try:

            india_priority_score = float(
                data.get(
                    "india_priority_score",
                    data.get(
                        "india_priority",
                        0,
                    ),
                )
                or 0
            )

        except (
            TypeError,
            ValueError,
        ):

            india_priority_score = 0

        return {
            "company": str(
                data.get(
                    "company",
                    "",
                )
                or ""
            ),

            "title": str(
                data.get(
                    "title",
                    "",
                )
                or ""
            ),

            "location": str(
                data.get(
                    "location",
                    "",
                )
                or ""
            ),

            "description": str(
                data.get(
                    "description",
                    "",
                )
                or ""
            ),

            "job_url": str(
                job_url
                or ""
            ),

            "source": str(
                data.get(
                    "source",
                    "Adzuna",
                )
                or "Adzuna"
            ),

            "salary_min": data.get(
                "salary_min"
            ),

            "salary_max": data.get(
                "salary_max"
            ),

            "match_score": existing_match_score,

            "matched_skills": matched_skills,

            "missing_skills": missing_skills,

            "why_suitable": why_suitable,

            "india_priority_score": india_priority_score,

            "is_indian_company": bool(
                data.get(
                    "is_indian_company",
                    False,
                )
            ),

            # Preserve any explicit job skills if supplied.
            "skills": data.get(
                "skills",
                [],
            ),

            "required_skills": data.get(
                "required_skills",
                [],
            ),
        }