from typing import List, Dict


class CareerProfile:
    """
    Represents a universal professional profile.

    This model is designed to support
    any profession.
    """

    def __init__(
        self,
        profession="",
        role="",
        industry="",
        seniority="",
        competencies=None,
        experience=None,
        education=None,
        certifications=None,
        achievements=None,
        portfolio=None,
    ):

        self.profession = profession

        self.role = role

        self.industry = industry

        self.seniority = seniority


        self.competencies = (
            competencies 
            if competencies 
            else {
                "technical": [],
                "tools": [],
                "soft_skills": [],
                "domain_knowledge": [],
                "languages": []
            }
        )


        self.experience = experience if experience else []

        self.education = education if education else []

        self.certifications = certifications if certifications else []

        self.achievements = achievements if achievements else []

        self.portfolio = portfolio if portfolio else []



    @classmethod
    def from_dict(cls, data: Dict):

        return cls(

            profession=data.get(
                "profession",
                ""
            ),

            role=data.get(
                "role",
                ""
            ),

            industry=data.get(
                "industry",
                ""
            ),

            seniority=data.get(
                "seniority",
                ""
            ),

            competencies=data.get(
                "competencies",
                {}
            ),

            experience=data.get(
                "experience",
                []
            ),

            education=data.get(
                "education",
                []
            ),

            certifications=data.get(
                "certifications",
                []
            ),

            achievements=data.get(
                "achievements",
                []
            ),

            portfolio=data.get(
                "portfolio",
                []
            )
        )


    def to_dict(self):

        return {

            "profession": self.profession,

            "role": self.role,

            "industry": self.industry,

            "seniority": self.seniority,

            "competencies": self.competencies,

            "experience": self.experience,

            "education": self.education,

            "certifications": self.certifications,

            "achievements": self.achievements,

            "portfolio": self.portfolio
        }