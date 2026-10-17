"""
ATS Report Model

This model represents the final output of the ATS Engine.
It stores the ATS score, section-wise breakdown,
strengths, weaknesses, and improvement suggestions.
"""


class ATSReport:
    """
    Represents the final ATS evaluation report.
    """

    def __init__(
        self,
        score=0,
        grade="F",
        strengths=None,
        weaknesses=None,
        improvements=None,
        score_breakdown=None,
    ):
        """
        Initialize the ATS Report.

        Parameters
        ----------
        score : float
            Overall ATS score.

        grade : str
            ATS grade (A+, A, B, C, D, F).

        strengths : list
            Positive aspects of the resume.

        weaknesses : list
            Areas where the resume is lacking.

        improvements : list
            Recommended improvements.

        score_breakdown : dict
            Section-wise ATS scores.
        """

        self.score = score
        self.grade = grade

        self.strengths = strengths or []

        self.weaknesses = weaknesses or []

        self.improvements = improvements or []

        self.score_breakdown = score_breakdown or {}

    def to_dict(self):
        """
        Convert the ATS report into a dictionary.
        """

        return {
            "score": self.score,
            "grade": self.grade,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "improvements": self.improvements,
            "score_breakdown": self.score_breakdown,
        }

    def __str__(self):
        """
        Human-readable representation of the ATS report.
        """

        return (
            f"ATSReport("
            f"score={self.score}, "
            f"grade='{self.grade}')"
        )