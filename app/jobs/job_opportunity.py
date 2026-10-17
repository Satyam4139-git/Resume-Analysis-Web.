class JobOpportunity:
    """
    Represents a real external job opportunity.

    Job
        = user-supplied target job description.

    JobOpportunity
        = real job posting obtained from an external
          job-search provider.
    """

    def __init__(
        self,
        company="",
        title="",
        location="",
        description="",
        job_url="",
        source="",
        salary_min=None,
        salary_max=None,
        match_score=0,
        matched_skills=None,
        missing_skills=None,
        why_suitable=None,
        india_priority_score=0,
        is_indian_company=False,
    ):

        self.company = (
            company
            if isinstance(company, str)
            else str(company)
        )

        self.title = (
            title
            if isinstance(title, str)
            else str(title)
        )

        self.location = (
            location
            if isinstance(location, str)
            else str(location)
        )

        self.description = (
            description
            if isinstance(description, str)
            else str(description)
        )

        self.job_url = (
            job_url
            if isinstance(job_url, str)
            else str(job_url)
        )

        self.source = (
            source
            if isinstance(source, str)
            else str(source)
        )

        self.salary_min = salary_min
        self.salary_max = salary_max

        self.match_score = float(
            match_score or 0
        )

        self.matched_skills = (
            matched_skills
            if isinstance(matched_skills, list)
            else []
        )

        self.missing_skills = (
            missing_skills
            if isinstance(missing_skills, list)
            else []
        )

        self.why_suitable = (
            why_suitable
            if isinstance(why_suitable, list)
            else []
        )

        self.india_priority_score = float(
            india_priority_score or 0
        )

        self.is_indian_company = bool(
            is_indian_company
        )

    def to_dict(self):
        """
        Convert opportunity to a JSON-friendly dictionary.
        """

        return {
            "company": self.company,
            "title": self.title,
            "location": self.location,
            "description": self.description,
            "job_url": self.job_url,
            "source": self.source,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "match_score": self.match_score,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "why_suitable": self.why_suitable,
            "india_priority_score": self.india_priority_score,
            "is_indian_company": self.is_indian_company,
        }