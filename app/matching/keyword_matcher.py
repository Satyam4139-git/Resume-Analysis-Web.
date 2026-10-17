class KeywordMatcher:

    @staticmethod
    def match(resume_skills, keywords):

        resume = {s.lower().strip() for s in resume_skills}
        keys = {k.lower().strip() for k in keywords}

        matched = sorted(resume & keys)
        missing = sorted(keys - resume)

        score = 100

        if keys:
            score = round(len(matched) / len(keys) * 100)

        return {
            "score": score,
            "matched": matched,
            "missing": missing,
        }