from typing import List, Dict


class JobRecommendationEngine:
    """
    Recommends suitable career roles based on the
    candidate's current resume.

    This engine does NOT search live job openings yet.

    It determines:
        - Suitable roles
        - Match score
        - Matched skills
        - Missing skills
        - Career fit

    Live company/job opening integration will be
    added in a later phase.
    """

    # ==========================================================
    # ROLE KNOWLEDGE BASE
    # ==========================================================

    ROLE_PROFILES = {

        "Backend Engineer": {
            "skills": [
                "python",
                "fastapi",
                "sql",
                "rest api",
                "git",
                "docker",
                "aws"
            ],
            "keywords": [
                "backend",
                "api",
                "server",
                "database"
            ]
        },

        "Python Developer": {
            "skills": [
                "python",
                "sql",
                "git",
                "rest api",
                "django",
                "flask"
            ],
            "keywords": [
                "python",
                "backend",
                "automation",
                "development"
            ]
        },

        "Full Stack Developer": {
            "skills": [
                "python",
                "javascript",
                "html",
                "css",
                "react",
                "sql",
                "git"
            ],
            "keywords": [
                "frontend",
                "backend",
                "full stack",
                "web development"
            ]
        },

        "Software Engineer": {
            "skills": [
                "python",
                "java",
                "c++",
                "sql",
                "git",
                "data structures",
                "algorithms"
            ],
            "keywords": [
                "software",
                "development",
                "programming",
                "engineering"
            ]
        },

        "Data Analyst": {
            "skills": [
                "python",
                "sql",
                "excel",
                "pandas",
                "numpy",
                "statistics",
                "data visualization"
            ],
            "keywords": [
                "data",
                "analysis",
                "analytics",
                "reporting"
            ]
        },

        "Machine Learning Engineer": {
            "skills": [
                "python",
                "machine learning",
                "tensorflow",
                "pytorch",
                "numpy",
                "pandas",
                "scikit-learn",
                "sql"
            ],
            "keywords": [
                "machine learning",
                "ml",
                "model",
                "artificial intelligence"
            ]
        },

        "DevOps Engineer": {
            "skills": [
                "linux",
                "docker",
                "kubernetes",
                "aws",
                "git",
                "ci/cd",
                "terraform"
            ],
            "keywords": [
                "devops",
                "deployment",
                "cloud",
                "infrastructure"
            ]
        },

        "Cloud Engineer": {
            "skills": [
                "aws",
                "azure",
                "gcp",
                "docker",
                "kubernetes",
                "linux",
                "terraform"
            ],
            "keywords": [
                "cloud",
                "infrastructure",
                "deployment",
                "cloud computing"
            ]
        },

        "Cybersecurity Analyst": {
            "skills": [
                "linux",
                "networking",
                "python",
                "wireshark",
                "nmap",
                "siem",
                "security"
            ],
            "keywords": [
                "cybersecurity",
                "security",
                "network security",
                "threat"
            ]
        }
    }

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self):

        self.roles = self.ROLE_PROFILES

    # ==========================================================
    # NORMALIZE SKILLS
    # ==========================================================

    @staticmethod
    def _normalize_skills(
        skills
    ) -> set:

        if not skills:

            return set()

        normalized = set()

        for skill in skills:

            if not isinstance(
                skill,
                str
            ):
                continue

            cleaned = (
                skill
                .strip()
                .lower()
            )

            if cleaned:

                normalized.add(
                    cleaned
                )

        return normalized

    # ==========================================================
    # CALCULATE ROLE MATCH
    # ==========================================================

    def _calculate_match(
        self,
        resume_skills,
        role_skills
    ):

        resume_set = self._normalize_skills(
            resume_skills
        )

        role_set = self._normalize_skills(
            role_skills
        )

        if not role_set:

            return {
                "score": 0,
                "matched": [],
                "missing": []
            }

        matched = sorted(
            resume_set.intersection(
                role_set
            )
        )

        missing = sorted(
            role_set.difference(
                resume_set
            )
        )

        score = round(
            (
                len(matched)
                /
                len(role_set)
            )
            * 100,
            2
        )

        return {
            "score": score,
            "matched": matched,
            "missing": missing
        }

    # ==========================================================
    # RECOMMEND ROLES
    # ==========================================================

    def recommend(
        self,
        resume
    ) -> List[Dict]:
        """
        Analyze the resume and return suitable
        career roles.

        Parameters
        ----------
        resume:
            Resume model containing skills and
            career profile.

        Returns
        -------
        List[Dict]
            Recommended career roles.
        """

        if resume is None:

            return []

        resume_skills = getattr(
            resume,
            "skills",
            []
        )

        recommendations = []

        # ======================================================
        # CHECK EVERY ROLE
        # ======================================================

        for role_name, profile in self.roles.items():

            result = self._calculate_match(
                resume_skills,
                profile["skills"]
            )

            # Only recommend roles with
            # meaningful skill compatibility.

            if result["score"] < 30:

                continue

            recommendations.append({

                "role": role_name,

                "match_score": result["score"],

                "matched_skills": (
                    result["matched"]
                ),

                "missing_skills": (
                    result["missing"]
                ),

                "reason": self._generate_reason(
                    result["score"],
                    result["matched"]
                )
            })

        # ======================================================
        # SORT BY MATCH SCORE
        # ======================================================

        recommendations.sort(
            key=lambda item:
                item["match_score"],
            reverse=True
        )

        return recommendations

    # ==========================================================
    # GENERATE REASON
    # ==========================================================

    @staticmethod
    def _generate_reason(
        score,
        matched_skills
    ):

        if score >= 80:

            return (
                "Strong career fit based on "
                "the candidate's existing skills."
            )

        if score >= 60:

            return (
                "Good career fit. The candidate "
                "already has several relevant skills."
            )

        if score >= 40:

            return (
                "Potential career option, but "
                "additional skills are recommended."
            )

        return (
            "Possible career direction with "
            "significant skill development required."
        )