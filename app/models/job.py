class Job:
    """
    Represents a parsed Job Description.

    This model stores the information extracted
    from a company + role using AI.
    """

    def __init__(
        self,
        title="",
        company="",
        skills=None,
        experience_required="",
        education_required=None,
        responsibilities=None,
        keywords=None,
        summary=""
    ):

        self.title = (
            title
            if isinstance(title, str)
            else str(title)
        )

        self.company = (
            company
            if isinstance(company, str)
            else str(company)
        )

        self.skills = self._normalize_string_list(
            skills
        )

        self.experience_required = (
            experience_required
            if isinstance(experience_required, str)
            else str(experience_required)
        )

        self.education_required = (
            self._normalize_string_list(
                education_required
            )
        )

        self.responsibilities = (
            self._normalize_string_list(
                responsibilities
            )
        )

        self.keywords = (
            self._normalize_string_list(
                keywords
            )
        )

        self.summary = (
            summary
            if isinstance(summary, str)
            else str(summary)
        )

    # ==========================================================
    # NORMALIZATION
    # ==========================================================

    @staticmethod
    def _normalize_string_list(value):

        if value is None:
            return []

        if not isinstance(value, list):

            return [str(value)]

        result = []

        for item in value:

            if isinstance(item, str):

                cleaned = item.strip()

                if cleaned:
                    result.append(cleaned)

                continue

            if isinstance(item, dict):

                possible_keys = [
                    "name",
                    "skill",
                    "keyword",
                    "title",
                    "value",
                    "text",
                    "description",
                ]

                extracted = None

                for key in possible_keys:

                    if key in item and item[key] is not None:

                        extracted = item[key]

                        break

                if extracted is not None:

                    result.append(
                        str(extracted).strip()
                    )

                else:

                    result.append(
                        str(item)
                    )

                continue

            result.append(
                str(item)
            )

        return result

    # ==========================================================
    # FROM DICT
    # ==========================================================

    @classmethod
    def from_dict(cls, data):
        """
        Creates Job object from AI JSON response.
        """

        if not isinstance(data, dict):

            raise ValueError(
                "Job data must be a dictionary."
            )

        return cls(

            title=data.get(
                "title",
                ""
            ),

            company=data.get(
                "company",
                ""
            ),

            skills=data.get(
                "skills",
                []
            ),

            experience_required=data.get(
                "experience_required",
                ""
            ),

            education_required=data.get(
                "education_required",
                []
            ),

            responsibilities=data.get(
                "responsibilities",
                []
            ),

            keywords=data.get(
                "keywords",
                []
            ),

            summary=data.get(
                "summary",
                ""
            )
        )

    # ==========================================================
    # TO DICT
    # ==========================================================

    def to_dict(self):
        """
        Converts Job object into dictionary.
        """

        return {

            "title": self.title,

            "company": self.company,

            "skills": self.skills,

            "experience_required":
                self.experience_required,

            "education_required":
                self.education_required,

            "responsibilities":
                self.responsibilities,

            "keywords":
                self.keywords,

            "summary":
                self.summary
        }