from app.models.job import Job
from app.core.config import DEVELOPMENT_MODE
from app.core.logger import logger
from app.services.ai_service import AIService


class JobParser:
    """
    Converts a job description into a structured Job model.
    """

    def __init__(self):
        self.ai_service = AIService()

        logger.info(
            "JobParser initialized. Development mode: %s",
            DEVELOPMENT_MODE
        )

    def parse(
        self,
        company,
        role,
        job_description,
    ):
        """
        Parse a job description into a Job object.
        """

        logger.info(
            "Generating job profile"
        )

        # ==================================================
        # DEVELOPMENT MODE
        # ==================================================

        if DEVELOPMENT_MODE:

            logger.info(
                "Using mock job profile"
            )

            data = {

                "title": role,

                "company": company,

                "skills": [
                    "python",
                    "fastapi",
                    "docker",
                    "aws",
                    "redis"
                ],

                "keywords": [
                    "backend",
                    "api",
                    "cloud"
                ],

                "responsibilities": [
                    "Build APIs",
                    "Develop backend services"
                ],

                "experience_required": "1-2 years",

                "education_required": [],

                "summary": (
                    f"Mock {role} position at {company}."
                ),

                "learning_topics": [
                    "Docker",
                    "AWS",
                    "Redis"
                ]
            }

            return Job.from_dict(data)

        # ==================================================
        # VALIDATION
        # ==================================================

        if not company or not company.strip():

            raise ValueError(
                "Company name is required."
            )

        if not role or not role.strip():

            raise ValueError(
                "Job role is required."
            )

        if not job_description or not job_description.strip():

            raise ValueError(
                "A job description is required for production analysis."
            )

        # ==================================================
        # AI PROMPT
        # ==================================================

        prompt = f"""
Extract the job information below into JSON.

Return ONLY valid JSON.
Do not use markdown.
Do not use ```.

Use exactly this schema:

{{
    "title": "",
    "company": "",
    "skills": [],
    "experience_required": "",
    "education_required": [],
    "responsibilities": [],
    "keywords": [],
    "summary": ""
}}

Rules:

- Use only information present in the job description.
- Do not invent skills.
- Do not invent experience.
- Do not invent education.
- Keep arrays short and relevant.
- If information is missing, use an empty string or empty array.
- Return exactly one JSON object.

Company: {company}

Role: {role}

Job Description:
{job_description}
"""

        logger.info(
            "Sending job description to AI for structured parsing."
        )

        # ==================================================
        # AI REQUEST
        # ==================================================

        data = self.ai_service.send_json_prompt(
            prompt,
            max_tokens=700,
        )

        # ==================================================
        # VALIDATE AI RESPONSE
        # ==================================================

        if not isinstance(data, dict):

            logger.error(
                "AI returned invalid job response: %s",
                type(data).__name__
            )

            raise ValueError(
                "AI did not return a valid job JSON object."
            )

        logger.info(
            "AI job JSON received successfully."
        )

        # ==================================================
        # ENSURE REQUIRED FIELDS
        # ==================================================

        data.setdefault(
            "title",
            role
        )

        data.setdefault(
            "company",
            company
        )

        data.setdefault(
            "skills",
            []
        )

        data.setdefault(
            "experience_required",
            ""
        )

        data.setdefault(
            "education_required",
            []
        )

        data.setdefault(
            "responsibilities",
            []
        )

        data.setdefault(
            "keywords",
            []
        )

        data.setdefault(
            "summary",
            ""
        )

        # ==================================================
        # CREATE MODEL
        # ==================================================

        try:

            job = Job.from_dict(
                data
            )

        except Exception as error:

            logger.exception(
                "Failed to create Job model."
            )

            raise ValueError(
                f"Failed to create Job model: {error}"
            ) from error

        logger.info(
            "Job model created successfully."
        )

        return job