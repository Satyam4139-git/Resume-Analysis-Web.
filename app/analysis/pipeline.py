from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

from app.parser.resume_parser import ResumeParser
from app.services.job_service import JobService
from app.services.job_opportunity_service import (
    JobOpportunityService,
)

from app.matching.matching_engine import MatchingEngine

from app.career.skill_gap_analyzer import SkillGapAnalyzer
from app.career.career_advisor_agent import CareerAdvisorAgent
from app.career.opportunity_engine import OpportunityEngine

from app.reviewer.review_service import ReviewService
from app.improver.improvement_service import ImprovementService

from app.development.mock_resume_loader import MockResumeLoader

from app.core.logger import logger


class AnalysisPipeline:
    """
    Complete Resume Analysis Pipeline.

    Flow:

        Resume
          ↓
        Resume Intelligence
          ↓
        Career Opportunities
          ↓
        Real Job Postings
          ↓
        Optional Target Job
          ↓
        ATS + Matching
          ↓
        Skill Gap
          ↓
        Career Recommendation
          ↓
        AI Resume Review
          ↓
        Resume Improvement
          ↓
        Final Report
    """

    def __init__(
        self,
        mode="production",
    ):

        self.mode = mode

        self.resume_parser = ResumeParser()

        self.job_service = JobService()

        self.job_opportunity_service = (
            JobOpportunityService()
        )

        self.review_service = ReviewService()

        self.improvement_service = (
            ImprovementService()
        )

        self.career_advisor = (
            CareerAdvisorAgent()
        )

        self.matching_engine = (
            MatchingEngine()
        )

        logger.info(
            "Pipeline initialized in %s mode",
            mode,
        )

    # =========================================================
    # MAIN ANALYSIS
    # =========================================================

    def analyze(
        self,
        resume_path,
        company=None,
        role=None,
        job_description=None,
        include_ai=True,
    ):

        logger.info(
            "Starting resume-first career analysis."
        )

        # =====================================================
        # STEP 1 — PARSE RESUME
        # =====================================================

        if self.mode == "development":

            resume = MockResumeLoader.load()

        else:

            resume = self.resume_parser.parse(
                resume_path
            )

        logger.info(
            "Resume parsed successfully."
        )

        # Job search is a network call that does not depend on anything
        # below, so it runs in the background while the rest is computed.
        pool = ThreadPoolExecutor(max_workers=2)

        jobs_future = pool.submit(
            self.job_opportunity_service.search_jobs,
            resume=resume,
        )

        # =====================================================
        # STEP 2 — CAREER OPPORTUNITIES
        # =====================================================

        try:

            opportunities = (
                OpportunityEngine.recommend(
                    resume
                )
            )

            if not opportunities:
                opportunities = []

        except Exception as error:

            logger.exception(
                "Career opportunity generation failed: %s",
                error,
            )

            opportunities = []

        # =====================================================
        # STEP 3 — REAL JOB POSTINGS
        # =====================================================

        job_postings = []

        try:

            job_postings = jobs_future.result(
                timeout=25
            )

            if not job_postings:
                job_postings = []

        except Exception as error:

            logger.exception(
                "Real job search failed: %s",
                error,
            )

            job_postings = []

        # =====================================================
        # DEFAULT VALUES
        # =====================================================

        job = None

        match_result = None

        ats_report = None

        skill_gap = {
            "score": 0,
            "matched": [],
            "partial": [],
            "missing": [],
            "additional": [],
            "priority_gaps": [],
            "recommended_actions": [],
            "target_role": (
                role
                or (
                    opportunities[0].get("role")
                    if opportunities
                    and isinstance(
                        opportunities[0],
                        dict,
                    )
                    else ""
                )
                or "Resume Profile"
            ),
        }

        # =====================================================
        # STEP 4 — TARGET JOB ANALYSIS
        # =====================================================

        has_target_job = all(
            [
                company,
                role,
                job_description,
            ]
        )

        if has_target_job:

            logger.info(
                "Target job supplied. "
                "Running target-job analysis."
            )

            try:

                # -------------------------------------------------
                # PARSE TARGET JOB
                # -------------------------------------------------

                job = self.job_service.get_target_job(
                    company,
                    role,
                    job_description,
                )

                logger.info(
                    "Target job parsed successfully."
                )

                # -------------------------------------------------
                # MATCHING
                # -------------------------------------------------

                matching = (
                    self.matching_engine.compare(
                        resume,
                        job,
                    )
                )

                match_result = matching.get(
                    "match_result"
                )

                ats_report = matching.get(
                    "ats_report"
                )

                # -------------------------------------------------
                # SKILL GAP
                # -------------------------------------------------

                try:

                    skill_gap = (
                        SkillGapAnalyzer.analyze(
                            resume.skills,
                            job.skills,
                        )
                    )

                    if not isinstance(
                        skill_gap,
                        dict,
                    ):
                        skill_gap = {}

                except Exception as error:

                    logger.exception(
                        "Target-job skill-gap analysis failed: %s",
                        error,
                    )

                    skill_gap = {}

                skill_gap.setdefault(
                    "score",
                    (
                        match_result.skill_coverage
                        if match_result
                        else 0
                    ),
                )

                skill_gap.setdefault(
                    "matched",
                    (
                        match_result.matched_skills
                        if match_result
                        else []
                    ),
                )

                skill_gap.setdefault(
                    "missing",
                    (
                        match_result.missing_skills
                        if match_result
                        else []
                    ),
                )

                skill_gap.setdefault(
                    "partial",
                    [],
                )

                skill_gap.setdefault(
                    "additional",
                    [],
                )

                skill_gap.setdefault(
                    "priority_gaps",
                    [],
                )

                skill_gap.setdefault(
                    "recommended_actions",
                    [],
                )

                skill_gap["target_role"] = role

                logger.info(
                    "Target-job ATS and skill-gap analysis completed."
                )

            except Exception as error:

                logger.exception(
                    "Target job analysis failed: %s",
                    error,
                )

                job = None
                match_result = None
                ats_report = None

        # =====================================================
        # STEP 5 — RESUME-LEVEL ATS SCORE
        # =====================================================
        #
        # IMPORTANT:
        #
        # If a target job was supplied and target-job matching
        # succeeded, the target-job ATS score is used.
        #
        # The generic resume ATS score is only used when there
        # is no target job or the target-job calculation failed.
        # =====================================================

        if ats_report is None:

            ats_report = self._calculate_resume_ats(
                resume
            )

            logger.info(
                "Resume-level ATS score generated: %s",
                ats_report.get(
                    "score"
                ),
            )

        # =====================================================
        # STEP 6 — RESUME-LEVEL SKILL GAP
        # =====================================================

        if not has_target_job:

            skill_gap = (
                self._build_resume_skill_gap(
                    resume,
                    opportunities,
                )
            )

        # =====================================================
        # STEP 7 — DETERMINE TARGET ROLE
        # =====================================================

        target_role = (
            role
            or (
                opportunities[0].get("role")
                if opportunities
                and isinstance(
                    opportunities[0],
                    dict,
                )
                else None
            )
            or (
                resume.career_profile.role
                if getattr(
                    resume,
                    "career_profile",
                    None,
                )
                else None
            )
            or "Target Role"
        )

        # =====================================================
        # STEP 10 — CAREER RECOMMENDATION
        # =====================================================

        try:

            recommendation = (
                self.career_advisor.recommend(
                    resume=resume,
                    opportunities=opportunities,
                    target_role=role,
                    target_score=(
                        match_result.overall_score
                        if match_result
                        else None
                    ),
                    missing_skills=skill_gap.get(
                        "missing",
                        [],
                    ),
                )
            )

        except Exception as error:

            logger.exception(
                "Career recommendation failed: %s",
                error,
            )

            recommendation = {}

        # =====================================================
        # STEP 11 — AI RESUME REVIEW
        # =====================================================

        review = None

        improvement = None

        if include_ai:

            review, improvement = self._run_ai_extras(resume)

        try:

            pass

        except Exception as error:

            logger.exception(
                "AI resume review failed: %s",
                error,
            )

            review = None

        # =====================================================
        # STEP 12 — RESUME IMPROVEMENT
        # =====================================================

        try:

            pass

        except Exception as error:

            logger.exception(
                "Resume improvement failed: %s",
                error,
            )

            improvement = None

        # =====================================================
        # STEP 13 — NORMALIZE REVIEW
        # =====================================================

        review_data = self._safe_to_dict(
            review
        )

        if not review_data and not include_ai:

            review_data = {
                "pending": True,
                "strengths": [],
                "weaknesses": [],
                "suggestions": [],
            }

        elif not review_data:

            review_data = {
                "score": 0,

                "strengths": [],

                "weaknesses": [
                    "AI resume review was temporarily unavailable."
                ],

                "suggestions": [
                    "Try running the analysis again."
                ],

                "feedback": (
                    "The resume was successfully parsed, "
                    "but the AI review service was temporarily "
                    "unavailable."
                ),
            }

        # =====================================================
        # STEP 14 — NORMALIZE IMPROVEMENT
        # =====================================================

        improvement_data = self._safe_to_dict(
            improvement
        )

        if not improvement_data and not include_ai:

            improvement_data = {"pending": True}

        elif not improvement_data:

            improvement_data = {
                "improvements": [
                    "Use clear section headings.",
                    "Include measurable achievements.",
                    "Keep technical skills easy for ATS systems to identify.",
                    "Use job-specific keywords when applying to a target role.",
                ]
            }

        # =====================================================
        # STEP 15 — FINAL REPORT
        # =====================================================

        pool.shutdown(wait=False)

        logger.info(
            "Resume-first career analysis completed."
        )

        return {

            "resume":
                resume.to_dict(),

            "job": (
                job.to_dict()
                if job
                else None
            ),

            "match_result": (
                match_result.to_dict()
                if match_result
                else None
            ),

            "ats_report":
                self._safe_to_dict(
                    ats_report
                ),

            "skill_gap":
                skill_gap,

            "career_opportunities":
                opportunities,

            "job_postings": [
                (
                    item.to_dict()
                    if hasattr(
                        item,
                        "to_dict",
                    )
                    else item
                )
                for item in job_postings
            ],

            "career_recommendation":
                recommendation,

            "ai_review":
                review_data,

            "resume_improvement":
                improvement_data,
        }

    # =========================================================
    # AI REVIEW + IMPROVEMENT (run together, with a time limit)
    # =========================================================

    def _run_ai_extras(self, resume):
        """Review and improvement tips, in parallel. Never raises."""

        with ThreadPoolExecutor(max_workers=2) as pool:

            review_future = pool.submit(self.review_service.review, resume)

            improvement_future = pool.submit(self.improvement_service.improve, resume)

            try:
                review = review_future.result(timeout=45)
            except Exception as error:
                logger.warning("AI resume review failed: %s", error)
                review = None

            try:
                improvement = improvement_future.result(timeout=45)
            except Exception as error:
                logger.warning("Resume improvement failed: %s", error)
                improvement = None

        return review, improvement

    def analyze_ai(self, resume_path):
        """
        Second phase: AI review + improvement tips only.

        The frontend calls this at the same time as analyze(include_ai=False)
        so the main results appear without waiting for the slow AI text.
        The resume parse is cached, so the AI parse is not repeated.
        """

        resume = self.resume_parser.parse(resume_path)

        review, improvement = self._run_ai_extras(resume)

        review_data = self._safe_to_dict(review) or {
            "strengths": [],
            "weaknesses": [
                "AI review was temporarily unavailable."
            ],
            "suggestions": [
                "Try analysing again in a minute."
            ],
        }

        improvement_data = self._safe_to_dict(improvement) or {
            "improvements": [
                "Use clear section headings.",
                "Include measurable achievements.",
                "Keep technical skills easy for ATS systems to identify.",
                "Use job-specific keywords when applying to a target role.",
            ]
        }

        return {
            "ai_review": review_data,
            "resume_improvement": improvement_data,
        }

    # =========================================================
    # GENERIC RESUME ATS
    # =========================================================

    @staticmethod
    def _calculate_resume_ats(
        resume,
    ):
        """
        Generic resume ATS-readiness score.

        This is intentionally separate from target-job ATS
        matching.

        Maximum = 100.
        """

        score = 0

        strengths = []

        weaknesses = []

        improvements = []

        contact_score = 0

        if getattr(
            resume,
            "name",
            None,
        ):
            contact_score += 5

        if getattr(
            resume,
            "email",
            None,
        ):
            contact_score += 5

        if getattr(
            resume,
            "phone",
            None,
        ):
            contact_score += 5

        score += contact_score

        if contact_score == 15:

            strengths.append(
                "Resume contains complete basic contact information."
            )

        else:

            weaknesses.append(
                "Some basic contact information is missing."
            )

        summary = getattr(
            resume,
            "summary",
            "",
        )

        if (
            summary
            and len(
                summary.strip()
            ) >= 50
        ):

            score += 15

            strengths.append(
                "Resume contains a clear professional summary."
            )

        else:

            weaknesses.append(
                "Professional summary is missing or too short."
            )

            improvements.append(
                "Add a concise professional summary."
            )

        skills = getattr(
            resume,
            "skills",
            [],
        )

        skill_count = len(
            skills
            if isinstance(
                skills,
                (list, tuple, set),
            )
            else (
                [skills]
                if skills
                else []
            )
        )

        if skill_count >= 10:

            score += 25

            strengths.append(
                "Resume contains a strong list of searchable skills."
            )

        elif skill_count >= 5:

            score += 18

            strengths.append(
                "Resume contains several searchable skills."
            )

        elif skill_count > 0:

            score += 10

            weaknesses.append(
                "Resume contains a limited number of searchable skills."
            )

        else:

            weaknesses.append(
                "No technical or professional skills were detected."
            )

        experience = getattr(
            resume,
            "experience",
            "",
        )

        if (
            experience
            and len(
                str(
                    experience
                ).strip()
            ) >= 80
        ):

            score += 20

            strengths.append(
                "Resume contains professional experience details."
            )

        elif experience:

            score += 10

            weaknesses.append(
                "Professional experience details could be expanded."
            )

        else:

            weaknesses.append(
                "Professional experience was not detected."
            )

        education = getattr(
            resume,
            "education",
            [],
        )

        if education:

            score += 15

            strengths.append(
                "Education information is present."
            )

        else:

            weaknesses.append(
                "Education information was not detected."
            )

        projects = getattr(
            resume,
            "projects",
            [],
        )

        project_count = len(
            projects
            if isinstance(
                projects,
                (list, tuple, set),
            )
            else (
                [projects]
                if projects
                else []
            )
        )

        if project_count >= 2:

            score += 10

            strengths.append(
                "Resume contains relevant projects."
            )

        elif project_count:

            score += 5

        else:

            weaknesses.append(
                "Projects were not detected."
            )

        score = max(
            0,
            min(
                100,
                round(
                    score,
                    2,
                ),
            ),
        )

        if score >= 90:
            grade = "A+"

        elif score >= 85:
            grade = "A"

        elif score >= 70:
            grade = "B"

        elif score >= 55:
            grade = "C"

        elif score >= 40:
            grade = "D"

        else:
            grade = "F"

        if not improvements:

            improvements = [
                "Tailor your resume keywords to each target job.",
                "Keep achievements measurable and specific.",
                "Use standard ATS-friendly section headings.",
            ]

        return {
            "score": score,

            "grade": grade,

            "strengths": strengths,

            "weaknesses": weaknesses,

            "improvements": improvements,

            "score_breakdown": {
                "contact_information": contact_score,

                "summary": (
                    15
                    if summary
                    and len(
                        summary.strip()
                    ) >= 50
                    else 0
                ),

                "skills": (
                    25
                    if skill_count >= 10
                    else (
                        18
                        if skill_count >= 5
                        else (
                            10
                            if skill_count
                            else 0
                        )
                    )
                ),

                "experience": (
                    20
                    if experience
                    and len(
                        str(
                            experience
                        ).strip()
                    ) >= 80
                    else (
                        10
                        if experience
                        else 0
                    )
                ),

                "education": (
                    15
                    if education
                    else 0
                ),

                "projects": (
                    10
                    if project_count >= 2
                    else (
                        5
                        if project_count
                        else 0
                    )
                ),
            },
        }

    # =========================================================
    # RESUME-LEVEL SKILL GAP
    # =========================================================

    @staticmethod
    def _build_resume_skill_gap(
        resume,
        opportunities,
    ):

        resume_skills = [
            str(
                skill
            ).strip()
            for skill in getattr(
                resume,
                "skills",
                [],
            )
            if skill
        ]

        recommended_role = (
            opportunities[0]
            if opportunities
            and isinstance(
                opportunities[0],
                dict,
            )
            else None
        )

        if recommended_role:

            matched = (
                recommended_role.get(
                    "matched_skills",
                    [],
                )
                or []
            )

            missing = (
                recommended_role.get(
                    "missing_skills",
                    [],
                )
                or []
            )

            additional = (
                recommended_role.get(
                    "additional_skills",
                    [],
                )
                or []
            )

            score = (
                recommended_role.get(
                    "match_score",
                    0,
                )
                or 0
            )

            role = (
                recommended_role.get(
                    "role"
                )
                or "Recommended Role"
            )

            return {
                "score": round(
                    float(
                        score
                    ),
                    2,
                ),

                "matched": matched,

                "partial": [],

                "missing": missing,

                "additional": (
                    additional
                    if additional
                    else resume_skills
                ),

                "priority_gaps": [
                    {
                        "skill": skill,
                        "priority": "high",
                        "reason": (
                            f"{skill} may be useful for "
                            f"the recommended {role} role."
                        ),
                    }
                    for skill in missing[:8]
                ],

                "recommended_actions": [
                    (
                        f"Develop practical knowledge of {skill}."
                    )
                    for skill in missing[:8]
                ],

                "target_role": role,
            }

        # IMPORTANT:
        #
        # There is no target requirement here.
        # Therefore it is NOT honest to report 100% skill match.
        #
        return {
            "score": 0,

            "matched": [],

            "partial": [],

            "missing": [],

            "additional": resume_skills,

            "priority_gaps": [],

            "recommended_actions": [],

            "target_role": "Resume Profile",
        }

    # =========================================================
    # SAFE SERIALIZATION
    # =========================================================

    @staticmethod
    def _safe_to_dict(
        value,
    ):

        if value is None:
            return None

        if hasattr(
            value,
            "to_dict",
        ):

            try:
                return value.to_dict()

            except Exception:
                return None

        if isinstance(
            value,
            dict,
        ):

            return value

        return value