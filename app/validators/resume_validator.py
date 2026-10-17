class ResumeValidator:
    """
    Validates AI-generated resume data.
    """

    @staticmethod
    def validate(data):

        if data is None:
            return None

        # Required fields
        data.setdefault("name", "")
        data.setdefault("email", "")
        data.setdefault("phone", "")
        data.setdefault("skills", [])
        data.setdefault("experience", "")
        data.setdefault("education", [])
        data.setdefault("projects", [])
        data.setdefault("resume_score", 0)
        data.setdefault("summary", "")

        return data