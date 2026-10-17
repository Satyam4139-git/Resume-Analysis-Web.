class EducationMatcher:
    """
    Matches the candidate's education with
    the job's education requirements.
    """

    @staticmethod
    def match(resume_education, job_education):
        """
        Compare resume education with required education.

        Parameters
        ----------
        resume_education : list
            Education from the resume.

        job_education : list
            Required education from the job.

        Returns
        -------
        int
            Match score (0–100).
        """

        # No education requirement
        if not job_education:
            return 100

        # No education in resume
        if not resume_education:
            return 0

        # Convert resume education into one lowercase string
        resume_text = " ".join(
            str(item).lower()
            for item in resume_education
        )

        # Check every required qualification
        for education in job_education:

            if str(education).lower() in resume_text:
                return 100

        return 0