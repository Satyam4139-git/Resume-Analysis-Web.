import re

from app.jobs.job_opportunity import JobOpportunity


class JobMatcher:
    """
    Matches a resume against real job opportunities.

    This is intentionally deterministic for the first
    implementation.

    Later we can replace/enhance this with an AI-based
    semantic matcher.
    """

    @staticmethod
    def normalize(value):

        if not isinstance(value, str):
            return ""

        return value.strip().lower()

    @classmethod
    def extract_resume_skills(
        cls,
        resume
    ):

        skills = set()

        for skill in resume.skills or []:

            if isinstance(skill, str):

                normalized = cls.normalize(
                    skill
                )

                if normalized:

                    skills.add(
                        normalized
                    )

        return skills

    @classmethod
    def extract_job_terms(
        cls,
        description
    ):

        if not description:
            return set()

        text = cls.normalize(
            description
        )

        # Common technical skills / technologies.
        known_terms = [
            "python",
            "java",
            "javascript",
            "typescript",
            "c++",
            "c#",
            "go",
            "rust",

            "fastapi",
            "django",
            "flask",
            "spring",
            "node.js",
            "nodejs",
            "react",
            "angular",
            "vue",

            "sql",
            "mysql",
            "postgresql",
            "mongodb",
            "redis",

            "rest api",
            "graphql",

            "git",
            "github",

            "docker",
            "kubernetes",

            "aws",
            "azure",
            "gcp",

            "linux",

            "tensorflow",
            "pytorch",
            "scikit-learn",

            "numpy",
            "pandas",

            "machine learning",
            "deep learning",
            "artificial intelligence",
            "ai",

            "nlp",
            "llm",

            "excel",
            "power bi",
            "tableau",
        ]

        matched_terms = set()

        for term in known_terms:

            if term in text:

                matched_terms.add(
                    term
                )

        return matched_terms

    @classmethod
    def calculate_match(
        cls,
        resume,
        opportunity
    ):

        resume_skills = (
            cls.extract_resume_skills(
                resume
            )
        )

        job_skills = (
            cls.extract_job_terms(
                opportunity.description
            )
        )

        if not job_skills:

            # If the posting doesn't contain
            # recognizable technical skills,
            # we don't pretend there is a
            # meaningful skill score.
            score = 0

            matched = []

            missing = []

        else:

            matched = sorted(
                resume_skills.intersection(
                    job_skills
                )
            )

            missing = sorted(
                job_skills.difference(
                    resume_skills
                )
            )

            score = round(
                (
                    len(matched)
                    /
                    len(job_skills)
                )
                * 100,
                1,
            )

        why_suitable = []

        if matched:

            why_suitable.append(
                "Your resume contains "
                + ", ".join(matched[:6])
                + ", which matches skills "
                "mentioned in this job posting."
            )

        if score >= 80:

            why_suitable.append(
                "Your technical skill profile "
                "shows strong alignment with "
                "this opportunity."
            )

        elif score >= 60:

            why_suitable.append(
                "Your resume has a good portion "
                "of the technical skills required "
                "for this opportunity."
            )

        elif score >= 40:

            why_suitable.append(
                "Your resume has some relevant "
                "skills, but additional skills "
                "may be required."
            )

        else:

            why_suitable.append(
                "This opportunity has limited "
                "skill overlap with the current "
                "resume."
            )

        if missing:

            why_suitable.append(
                "Skills to consider developing: "
                + ", ".join(missing[:5])
                + "."
            )

        opportunity.match_score = score

        opportunity.matched_skills = matched

        opportunity.missing_skills = missing[:8]

        opportunity.why_suitable = (
            why_suitable
        )

        return opportunity

    @classmethod
    def match_many(
        cls,
        resume,
        opportunities,
        limit=6,
    ):

        matched_opportunities = []

        for opportunity in opportunities:

            matched = cls.calculate_match(
                resume,
                opportunity,
            )

            matched_opportunities.append(
                matched
            )

        matched_opportunities.sort(
            key=lambda item: item.match_score,
            reverse=True,
        )

        return matched_opportunities[
            :limit
        ]