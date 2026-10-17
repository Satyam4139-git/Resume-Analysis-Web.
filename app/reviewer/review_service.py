from app.reviewer.ai_resume_reviewer import AIResumeReviewer


class ReviewService:

    """
    Service wrapper for Resume Reviewer Agent.
    """

    def __init__(self):

        self.agent = AIResumeReviewer()

    def review(self, resume):

        return self.agent.review(resume)