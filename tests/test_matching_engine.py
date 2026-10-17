from app.models.resume import Resume
from app.models.job import Job
from app.matching.matching_engine import MatchingEngine


resume = Resume(
    skills=["Python", "FastAPI", "SQL"],
    experience="2 years",
    education=["B.Tech Computer Science"],
)

job = Job(
    skills=["Python", "Docker", "FastAPI"],
    keywords=["Python", "Docker", "REST API"],
    experience="3 years",
    education="B.Tech",
)

result = MatchingEngine.compare(resume, job)

print("Overall Score:", result.overall_score)
print("Skill Score:", result.skill_score)
print("Keyword Score:", result.keyword_score)
print("Experience Score:", result.experience_score)
print("Education Score:", result.education_score)
print("Matched Skills:", result.matched_skills)
print("Missing Skills:", result.missing_skills)
print("Suggestions:", result.suggestions)