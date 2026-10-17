class AnalysisReport:
    """
    Stores the complete career analysis report.
    """

    def __init__(
        self,
        resume=None,
        job=None,
        match_result=None,
        ats_report=None,
        skill_gap=None,
        recommendation=None,
        career_opportunities=None,
        ai_review=None,
        resume_improvement=None,
    ):

        self.resume = resume

        self.job = job

        self.match_result = match_result

        self.ats_report = ats_report

        self.skill_gap = skill_gap

        self.recommendation = recommendation

        self.career_opportunities = (
            career_opportunities
        )

        self.ai_review = ai_review

        self.resume_improvement = (
            resume_improvement
        )

    def to_dict(self):

        return {

            "resume":
                self.resume.to_dict()
                if self.resume
                else None,

            "job":
                self.job.to_dict()
                if self.job
                else None,

            "match_result":
                self.match_result.to_dict()
                if self.match_result
                else None,

            "ats_report":
                self.ats_report.to_dict()
                if self.ats_report
                else None,

            "skill_gap":
                self.skill_gap,

            "career_recommendation":
                self.recommendation,

            "career_opportunities":
                self.career_opportunities,

            "ai_review":
                (
                    self.ai_review.to_dict()
                    if self.ai_review
                    else None
                ),

            "resume_improvement":
                (
                    self.resume_improvement.to_dict()
                    if self.resume_improvement
                    else None
                ),
        }