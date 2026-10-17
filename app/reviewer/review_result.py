class ReviewResult:
    """
    Stores the AI review of a resume.
    """

    def __init__(
        self,
        overall_score=0,
        strengths=None,
        weaknesses=None,
        suggestions=None,
        summary="",
    ):

        self.overall_score = overall_score

        self.strengths = strengths or []

        self.weaknesses = weaknesses or []

        self.suggestions = suggestions or []

        self.summary = summary

    @classmethod
    def from_dict(cls, data):

        return cls(
            overall_score=data.get("overall_score", 0),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            suggestions=data.get("suggestions", []),
            summary=data.get("summary", ""),
        )

    def to_dict(self):

        return {
            "overall_score": self.overall_score,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "suggestions": self.suggestions,
            "summary": self.summary,
        }