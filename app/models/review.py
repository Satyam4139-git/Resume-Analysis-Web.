class Review:
    def __init__(
        self,
        strengths,
        weaknesses,
        suggestions,
    ):
        self.strengths = strengths
        self.weaknesses = weaknesses
        self.suggestions = suggestions

    @classmethod
    def from_dict(cls, data):
        return cls(
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            suggestions=data.get("suggestions", []),
        )

    def to_dict(self):
        return {
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "suggestions": self.suggestions,
        }