class MatchResult:
    """
    Stores complete resume-job matching result.
    """

    def __init__(
        self,
        overall_score=0,
        skill_score=0,
        keyword_score=0,
        experience_score=0,
        education_score=0,
        matched_skills=None,
        missing_skills=None,
        matched_keywords=None,
        missing_keywords=None,
        suggestions=None,
    ):

        self.overall_score = overall_score

        self.skill_score = skill_score

        self.keyword_score = keyword_score

        self.experience_score = experience_score

        self.education_score = education_score

        self.matched_skills = (
            matched_skills
            if matched_skills
            else []
        )

        self.missing_skills = (
            missing_skills
            if missing_skills
            else []
        )

        self.matched_keywords = (
            matched_keywords
            if matched_keywords
            else []
        )

        self.missing_keywords = (
            missing_keywords
            if missing_keywords
            else []
        )

        self.suggestions = (
            suggestions
            if suggestions
            else []
        )

    @classmethod
    def from_dict(cls, data):

        return cls(
            overall_score=data.get(
                "overall_score",
                0,
            ),
            skill_score=data.get(
                "skill_score",
                0,
            ),
            keyword_score=data.get(
                "keyword_score",
                0,
            ),
            experience_score=data.get(
                "experience_score",
                0,
            ),
            education_score=data.get(
                "education_score",
                0,
            ),
            matched_skills=data.get(
                "matched_skills",
                [],
            ),
            missing_skills=data.get(
                "missing_skills",
                [],
            ),
            matched_keywords=data.get(
                "matched_keywords",
                [],
            ),
            missing_keywords=data.get(
                "missing_keywords",
                [],
            ),
            suggestions=data.get(
                "suggestions",
                [],
            ),
        )

    def to_dict(self):

        return {

            "overall_score": self.overall_score,

            "skill_score": self.skill_score,

            "keyword_score": self.keyword_score,

            "experience_score": self.experience_score,

            "education_score": self.education_score,

            "matched_skills": self.matched_skills,

            "missing_skills": self.missing_skills,

            "matched_keywords": self.matched_keywords,

            "missing_keywords": self.missing_keywords,

            "suggestions": self.suggestions,
        }