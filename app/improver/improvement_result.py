class ImprovementResult:
    """
    Stores AI resume improvement suggestions.
    """

    def __init__(
        self,
        improved_summary="",
        improved_skills=None,
        improved_projects=None,
        keywords_to_add=None,
        ats_tips=None,
    ):
        self.improved_summary = improved_summary

        self.improved_skills = improved_skills or []

        self.improved_projects = improved_projects or []

        self.keywords_to_add = keywords_to_add or []

        self.ats_tips = ats_tips or []

    @classmethod
    def from_dict(cls, data):

        return cls(
            improved_summary=data.get(
                "improved_summary", ""
            ),

            improved_skills=data.get(
                "improved_skills", []
            ),

            improved_projects=data.get(
                "improved_projects", []
            ),

            keywords_to_add=data.get(
                "keywords_to_add", []
            ),

            ats_tips=data.get(
                "ats_tips", []
            ),
        )

    def to_dict(self):

        return {
            "improved_summary": self.improved_summary,
            "improved_skills": self.improved_skills,
            "improved_projects": self.improved_projects,
            "keywords_to_add": self.keywords_to_add,
            "ats_tips": self.ats_tips,
        }