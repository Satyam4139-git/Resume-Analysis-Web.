class JobValidator:
    """
    Validates AI-generated job data.
    """

    REQUIRED_FIELDS = [
        "title",
        "company",
        "competencies",
    ]

    @classmethod
    def validate(cls, data):

        if not isinstance(data, dict):
            raise ValueError("Job data must be a dictionary.")

        for field in cls.REQUIRED_FIELDS:
            if field not in data:
                data[field] = {}

        return data