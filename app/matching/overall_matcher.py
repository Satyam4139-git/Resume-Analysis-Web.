class OverallMatcher:

    WEIGHTS = {
        "skills": 0.40,
        "keywords": 0.20,
        "experience": 0.20,
        "education": 0.20,
    }

    @classmethod
    def calculate(
        cls,
        skill_score,
        keyword_score,
        experience_score,
        education_score,
    ):

        overall = (
            skill_score * cls.WEIGHTS["skills"]
            + keyword_score * cls.WEIGHTS["keywords"]
            + experience_score * cls.WEIGHTS["experience"]
            + education_score * cls.WEIGHTS["education"]
        )

        return round(overall)