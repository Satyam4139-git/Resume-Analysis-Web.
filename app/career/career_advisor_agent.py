class CareerAdvisorAgent:
    """
    Generates career-level recommendations from
    the candidate's resume and opportunity analysis.
    """

    def recommend(
        self,
        resume,
        opportunities,
        target_role=None,
        target_score=None,
        missing_skills=None,
    ):

        if opportunities:

            best_role = opportunities[0]["role"]

        else:

            best_role = (
                target_role
                if target_role
                else (
                    resume.career_profile.role
                    if resume.career_profile
                    else "Software Professional"
                )
            )

        if target_score is not None:

            score = target_score

        elif opportunities:

            score = opportunities[0]["match_score"]

        else:

            score = 0

        missing_skills = (
            missing_skills
            if missing_skills
            else []
        )

        return {

            "recommended_role": best_role,

            "target_role": target_role or best_role,

            "current_level": self._level(score),

            "match_score": score,

            "focus_skills": missing_skills,

            "recommended_roles": opportunities,

            "advice": (
                "Strengthen the missing skills, "
                "build practical projects, "
                "improve ATS keywords, "
                "and prepare for technical and "
                "behavioral interviews."
            )
        }

    @staticmethod
    def _level(score):

        if score >= 85:
            return "Strong Candidate"

        if score >= 70:
            return "Job Ready"

        if score >= 55:
            return "Developing"

        return "Needs Improvement"