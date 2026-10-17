class CareerRecommendation:
    """
    Represents the final career recommendation.
    """

    def __init__(
        self,
        role="",
        readiness=0,
        estimated_weeks=0,
        priority_skills=None,
        recommended_project="",
        summary="",
    ):

        self.role = role
        self.readiness = readiness
        self.estimated_weeks = estimated_weeks

        self.priority_skills = (
            priority_skills
            if priority_skills
            else []
        )

        self.recommended_project = (
            recommended_project
        )

        self.summary = summary

    def to_dict(self):

        return {

            "role": self.role,

            "readiness": self.readiness,

            "estimated_weeks":
                self.estimated_weeks,

            "priority_skills":
                self.priority_skills,

            "recommended_project":
                self.recommended_project,

            "summary":
                self.summary,
        }