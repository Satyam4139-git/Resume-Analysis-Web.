from app.parser.job_parser import JobParser
from app.core.logger import logger


class JobService:
    """
    Service responsible for obtaining and parsing
    the target job.
    """

    def __init__(self):

        self.parser = JobParser()

        logger.info(
            "JobService initialized."
        )

    def get_target_job(
        self,
        company_name,
        role,
        job_description,
    ):
        """
        Parse the supplied job information
        and return a Job model.
        """

        logger.info(
            "Getting target job."
        )

        return self.parser.parse(
            company_name,
            role,
            job_description,
        )