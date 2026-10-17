"""
Career opportunity recommender (deterministic, no AI, instant).

Level-aware: a fresher and an engineer with 8 years of experience get
different roles, titles and explanations.
"""

from __future__ import annotations

import re
from typing import Dict, List, Set

from app.utils.seniority import LEVEL_NAMES, get_level


# --------------------------------------------------------------------------
# skill normalisation ("REST APIs", "restful" and "rest api" are one skill)
# --------------------------------------------------------------------------

ALIASES = {
    "rest apis": "rest api", "restful": "rest api", "restful api": "rest api",
    "restful apis": "rest api", "api": "rest api", "apis": "rest api",
    "postgres": "postgresql", "postgre sql": "postgresql",
    "js": "javascript", "ecmascript": "javascript", "node": "node.js",
    "nodejs": "node.js", "reactjs": "react", "react.js": "react",
    "angularjs": "angular", "vuejs": "vue", "vue.js": "vue",
    "ml": "machine learning", "dl": "deep learning",
    "scikit learn": "scikit-learn", "sklearn": "scikit-learn",
    "powerbi": "power bi", "power-bi": "power bi", "ms excel": "excel",
    "microsoft excel": "excel", "k8s": "kubernetes", "amazon web services": "aws",
    "google cloud": "gcp", "google cloud platform": "gcp", "ci cd": "ci/cd",
    "github actions": "ci/cd", "jenkins": "ci/cd", "cpp": "c++",
    "golang": "go", "tf": "tensorflow", "py torch": "pytorch",
    "natural language processing": "nlp", "large language models": "llm",
    "llms": "llm", "generative ai": "llm", "spring": "spring boot",
    "springboot": "spring boot", "dotnet": ".net", "asp.net": ".net",
    "data analysis": "data analytics", "mysql": "sql", "postgresql": "sql",
    "sql server": "sql", "sqlite": "sql", "oracle": "sql",
}


def norm(skill: str) -> str:
    key = re.sub(r"\s+", " ", str(skill).strip().lower())
    return ALIASES.get(key, key)


def norm_set(skills) -> Set[str]:
    return {norm(s) for s in (skills or []) if isinstance(s, str) and s.strip()}


# --------------------------------------------------------------------------
# role catalogue.  levels = (lowest, highest) candidate level the role suits
# 0 entry, 1 junior, 2 mid, 3 senior, 4 lead
# prefix=True -> title gets Junior / Senior ... according to candidate level
# --------------------------------------------------------------------------

def R(skills, keywords, levels=(0, 4), prefix=True):
    return {"skills": skills, "keywords": keywords, "levels": levels, "prefix": prefix}


ROLES: Dict[str, Dict] = {
    "Backend Developer": R(["python", "fastapi", "django", "flask", "sql", "rest api", "git", "docker"],
                           ["backend", "api", "server", "database", "microservices"]),
    "Python Developer": R(["python", "sql", "git", "rest api", "django", "flask"],
                          ["python", "backend", "automation", "scripting"]),
    "Software Engineer": R(["python", "java", "javascript", "git", "sql", "data structures"],
                           ["software", "developer", "engineering", "algorithms"]),
    "Full Stack Developer": R(["javascript", "react", "node.js", "html", "css", "sql", "rest api", "git"],
                              ["full stack", "frontend", "backend", "web"]),
    "Frontend Developer": R(["javascript", "react", "html", "css", "typescript", "angular", "vue", "git"],
                            ["frontend", "ui", "responsive", "web"]),
    "Java Developer": R(["java", "spring boot", "sql", "rest api", "git", "microservices"],
                        ["java", "spring", "backend"]),
    "Data Analyst": R(["sql", "excel", "power bi", "tableau", "python", "pandas", "data analytics"],
                      ["data", "analysis", "analytics", "reporting", "dashboard"]),
    "Business Intelligence Developer": R(["power bi", "tableau", "sql", "excel", "etl", "data analytics"],
                                         ["dashboard", "reporting", "bi", "visualization"], levels=(1, 4)),
    "Data Scientist": R(["python", "machine learning", "pandas", "numpy", "scikit-learn", "sql", "statistics"],
                        ["data science", "model", "statistics", "prediction"], levels=(0, 4)),
    "Machine Learning Engineer": R(["python", "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn", "docker"],
                                   ["machine learning", "ml", "model", "deployment"], levels=(1, 4)),
    "AI Engineer": R(["python", "machine learning", "deep learning", "llm", "nlp", "pytorch", "tensorflow"],
                     ["ai", "artificial intelligence", "llm", "nlp", "generative"], levels=(0, 4)),
    "Data Engineer": R(["python", "sql", "spark", "etl", "kafka", "aws", "airflow"],
                       ["pipeline", "etl", "data engineering", "warehouse", "big data"], levels=(1, 4)),
    "DevOps Engineer": R(["docker", "kubernetes", "aws", "linux", "ci/cd", "git", "terraform"],
                         ["devops", "deployment", "infrastructure", "automation", "cloud"], levels=(1, 4)),
    "Cloud Engineer": R(["aws", "azure", "gcp", "linux", "docker", "terraform", "networking"],
                        ["cloud", "infrastructure", "serverless"], levels=(1, 4)),
    "QA / Test Automation Engineer": R(["selenium", "python", "java", "sql", "git", "ci/cd"],
                                       ["testing", "qa", "automation", "quality"]),
    "Cyber Security Analyst": R(["cyber security", "networking", "linux", "wireshark", "python", "siem"],
                                ["security", "vulnerability", "threat", "penetration"]),
    "Android / Mobile Developer": R(["kotlin", "java", "android", "swift", "ios", "flutter", "react native"],
                                    ["mobile", "android", "ios", "app"]),
    # senior-track roles
    "Technical Lead": R(["python", "java", "microservices", "aws", "docker", "sql", "ci/cd", "git"],
                        ["lead", "architecture", "mentor", "design", "team"], levels=(3, 4), prefix=False),
    "Solutions Architect": R(["aws", "azure", "microservices", "docker", "kubernetes", "sql", "system design"],
                             ["architecture", "design", "scalable", "cloud", "solution"], levels=(3, 4), prefix=False),
    "Engineering Manager": R(["python", "java", "aws", "agile", "ci/cd", "microservices", "git"],
                             ["manager", "team", "lead", "roadmap", "stakeholder", "hiring"], levels=(4, 4), prefix=False),
}

PREFIX = {0: "Junior ", 1: "Junior ", 2: "", 3: "Senior ", 4: "Senior "}
# roles where an entry-level prefix reads badly are left as the plain title
NO_PREFIX_AT_LEVEL = {"Software Engineer": {2}}


class OpportunityEngine:
    """Recommend roles from the resume, taking experience level into account."""

    @classmethod
    def recommend(cls, resume, limit: int = 6) -> List[Dict]:

        level, years = get_level(resume)

        skills = norm_set(getattr(resume, "skills", []))

        resume_text = " ".join([
            getattr(resume, "summary", "") or "",
            getattr(resume, "experience", "") or "",
            " ".join(getattr(resume, "projects", []) or []),
            " ".join(getattr(resume, "skills", []) or []),
        ]).lower()

        if not skills and not resume_text.strip():
            return []

        results = []

        for base, profile in ROLES.items():

            low, high = profile["levels"]

            # A role far outside the candidate's level is not shown at all:
            # no Engineering Manager for a fresher, no "Junior" for 8 years.
            if level < low - 1 or level > high + 1:
                continue

            required = norm_set(profile["skills"])
            matched = sorted(skills & required)
            missing = sorted(required - skills)

            skill_score = len(matched) / len(required) * 100 if required else 0

            hits = sum(1 for k in profile["keywords"] if k in resume_text)
            keyword_score = hits / len(profile["keywords"]) * 100

            score = skill_score * 0.75 + keyword_score * 0.25

            # level fit
            fit = 1.0
            if level < low:
                fit = 0.8                 # a stretch
            elif level > high:
                fit = 0.85                # slightly below the candidate
            elif level >= 3 and low >= 3:
                fit = 1.08                # senior-track role for a senior person

            score = round(min(score * fit, 99))

            if score < 30:
                continue

            title = base
            if profile["prefix"]:
                prefix = PREFIX.get(level, "")
                if level in NO_PREFIX_AT_LEVEL.get(base, set()):
                    prefix = ""
                title = prefix + base

            why = []
            if matched:
                why.append(f"You already have {len(matched)} of {len(required)} key skills for this role.")
            if low <= level <= high:
                why.append(
                    f"Fits your experience level ({LEVEL_NAMES[level]}"
                    + (f", about {years:g} years)." if years >= 1 else ").")
                )
            elif level < low:
                why.append("A step up from your current level, so expect to grow into it.")
            else:
                why.append("Below your current level, but a possible way into this field.")

            results.append({
                "role": title,
                "base_role": base,
                "level": LEVEL_NAMES[level],
                "experience_years": years,
                "match_score": score,
                "matched_skills": matched[:8],
                "missing_skills": missing[:6],
                "why": why,
                "readiness": cls._readiness(score),
            })

        results.sort(key=lambda r: r["match_score"], reverse=True)
        return results[:limit]

    @staticmethod
    def _readiness(score):
        if score >= 85:
            return "Strong Match"
        if score >= 70:
            return "Good Match"
        if score >= 55:
            return "Possible Match"
        return "Worth Building Towards"
