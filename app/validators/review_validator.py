class ReviewValidator:

    @staticmethod
    def validate(data):

        return {
            "strengths": data.get("strengths", []),
            "weaknesses": data.get("weaknesses", []),
            "suggestions": data.get("suggestions", []),
        }