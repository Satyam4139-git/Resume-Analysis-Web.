from app.models.resume import Resume


class MockResumeLoader:
    """
    Loads sample resume data without using AI.

    Used during development to avoid
    external API dependency.
    """


    @staticmethod
    def load():

        resume_data = {

            "name": "Rahul Sharma",

            "email": "rahul@example.com",

            "phone": "9999999999",

            "skills": [
                "Python",
                "FastAPI",
                "Git",
                "SQL"
            ],

            "experience":
                "Backend Developer Intern",

            "education": [
                "B.Tech Computer Science"
            ],

            "projects": [
                "FastAPI REST API",
                "AI Resume Analyzer"
            ],

            "resume_score": 82,

            "summary":
                "Backend developer skilled in Python APIs and databases.",


            "career_profile": {

                "profession": "Technology",

                "role": "Backend Engineer",

                "industry": "Software",

                "seniority": "Junior",

                "competencies": {

                    "technical": [
                        "Python",
                        "FastAPI",
                        "SQL"
                    ],

                    "tools": [
                        "Git"
                    ]
                },

                "experience": [],

                "education": [
                    "B.Tech Computer Science"
                ]
            }
        }


        return Resume.from_dict(
            resume_data
        )