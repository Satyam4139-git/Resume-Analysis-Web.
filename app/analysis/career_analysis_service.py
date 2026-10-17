
from app.analysis.pipeline import AnalysisPipeline


class CareerAnalysisService:
    """
    Service layer for the unified career analysis pipeline.

    This class provides a clean public interface for
    resume-first career analysis.
    """

    def __init__(
        self,
        mode="production",
    ):

        self.pipeline = AnalysisPipeline(
            mode=mode
        )


    def analyze(
        self,
        resume_path,
        company=None,
        role=None,
        job_description=None,
        include_ai=True,
    ):
        """
        Run complete career analysis.

        Parameters
        ----------
        resume_path : str
            Path returned by resume upload endpoint.

        company : str, optional
            Target company.

        role : str, optional
            Target role.

        job_description : str, optional
            Target job description.

        Returns
        -------
        dict
            Complete career analysis.
        """

        return self.pipeline.analyze(
            resume_path=resume_path,
            company=company,
            role=role,
            job_description=job_description,
            include_ai=include_ai,
        )

    def analyze_ai(
        self,
        resume_path,
    ):
        """AI review + improvement tips only (second, slower phase)."""

        return self.pipeline.analyze_ai(
            resume_path
        )
