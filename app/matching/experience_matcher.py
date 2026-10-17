import re


class ExperienceMatcher:

    @staticmethod
    def _extract_years(text):

        if not text:
            return 0

        match = re.search(r"(\d+)", text)

        if match:
            return int(match.group(1))

        return 0

    @classmethod
    def match(cls, resume_exp, job_exp):

        resume_years = cls._extract_years(resume_exp)
        job_years = cls._extract_years(job_exp)

        if job_years == 0:
            return 100

        score = min(
            round(resume_years / job_years * 100),
            100,
        )

        return score