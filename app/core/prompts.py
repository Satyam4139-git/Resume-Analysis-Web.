"""
AI PROMPTS
==========

Centralized prompt definitions for the Resume Analyzer.

All prompts used by AI-powered services should live in this file.

IMPORTANT:
- Prompts that use Python .format() must escape JSON braces as {{ and }}.
- AI responses must follow the JSON structures requested below.
- Prompts must not ask the AI to invent candidate information.
"""


# ==============================================================
# RESUME PARSER PROMPT
# ==============================================================

RESUME_PARSER_PROMPT = """
You are an expert resume parsing and career-profile extraction system.

Your task is to analyze the resume text provided below and extract
structured information from it.

IMPORTANT RULES:

1. Return ONLY valid JSON.
2. Do NOT return markdown.
3. Do NOT use ```json or ``` blocks.
4. Do NOT include explanations outside the JSON object.
5. Do NOT invent information.
6. Only extract information explicitly supported by the resume.
7. If information is unavailable, use an empty string, empty list,
   or appropriate empty value.
8. Preserve factual information from the resume.
9. Extract skills from the entire resume, including skills mentioned
   inside projects, experience, education, certifications, and
   technical sections.
10. Do not confuse projects with employment experience.
11. Do not create fake companies, dates, degrees, skills, or positions.

Return EXACTLY this JSON structure:

{{
    "name": "",
    "email": "",
    "phone": "",

    "skills": [],

    "experience": "",

    "education": [],

    "projects": [],

    "resume_score": 0,

    "summary": "",

    "career_profile": {{
        "profession": "",
        "role": "",
        "industry": "",
        "seniority": "",
        "competencies": {{
            "technical": [],
            "tools": []
        }},
        "experience": [],
        "education": []
    }}
}}

FIELD RULES:

name:
Extract the candidate's full name.

email:
Extract the candidate's email address.

phone:
Extract the candidate's phone number.

skills:
Return a list of relevant technical and professional skills
explicitly supported by the resume.

experience:
Return a concise text representation of the candidate's
professional employment experience.

education:
Return a list of education records.

Each education record should preferably contain:

{{
    "institution": "",
    "degree": "",
    "field": "",
    "dates": "",
    "status": ""
}}

projects:
Return a list containing the names/titles of projects explicitly
mentioned in the resume.

resume_score:
Always return 0.

The application calculates the actual resume score separately.

summary:
Extract or create a concise professional summary using ONLY
information supported by the resume.

career_profile:
Determine the candidate's most likely professional profile
based ONLY on evidence contained in the resume.

profession:
The broad professional domain.

role:
The most suitable current/target role suggested by the resume.

industry:
Industry if clearly supported by the resume.
Otherwise return an empty string.

seniority:
Examples:
"Intern"
"Entry Level"
"Junior"
"Mid Level"
"Senior"

Only assign seniority when reasonably supported by the resume.
Otherwise return an empty string.

competencies.technical:
Technical skills relevant to the candidate's career profile.

competencies.tools:
Tools, platforms, software, databases, and development tools.

career_profile.experience:
Return structured experience records if enough information is
available.

career_profile.education:
Return structured education records if enough information is
available.

RESUME TEXT:

{resume}
"""


# ==============================================================
# AI RESUME REVIEW PROMPT
# ==============================================================

AI_REVIEW_PROMPT = """
You are a senior professional resume reviewer and ATS specialist.

Analyze the resume provided below.

Your task is to identify:

- strengths
- weaknesses
- actionable improvements
- ATS-related problems
- formatting/content issues
- career positioning issues

IMPORTANT RULES:

1. Return ONLY valid JSON.
2. Do NOT return markdown.
3. Do NOT use code fences.
4. Do NOT include explanations outside JSON.
5. Do NOT invent candidate information.
6. Base every observation on the provided resume.
7. Recommendations may suggest improvements, but must not claim
   the candidate possesses skills or experience that are not present.

Return EXACTLY this structure:

{{
    "strengths": [],
    "weaknesses": [],
    "suggestions": []
}}

strengths:
List the strongest aspects of the resume.

Maximum 8 items.

weaknesses:
List important weaknesses or missing elements.

Maximum 8 items.

suggestions:
Provide specific, actionable recommendations.

Maximum 10 items.

RESUME:

{resume}
"""


# ==============================================================
# JOB PARSER PROMPT
# ==============================================================

JOB_PARSER_PROMPT = """
You are an expert job-description parsing system.

Analyze the job description below and extract structured information.

IMPORTANT RULES:

1. Return ONLY valid JSON.
2. Do NOT return markdown.
3. Do NOT invent requirements.
4. Extract only information supported by the job description.
5. If information is unavailable, use an empty string or empty list.

Return EXACTLY:

{{
    "title": "",
    "company": "",
    "location": "",
    "description": "",
    "required_skills": [],
    "preferred_skills": [],
    "experience": "",
    "education": [],
    "responsibilities": [],
    "keywords": []
}}

JOB DESCRIPTION:

{job_description}
"""


# ==============================================================
# CAREER PROFILE PROMPT
# ==============================================================

CAREER_PROFILE_PROMPT = """
You are an expert career profiling system.

Analyze the resume and determine the candidate's professional
career profile.

Return ONLY valid JSON.

Return EXACTLY:

{{
    "profession": "",
    "role": "",
    "industry": "",
    "seniority": "",
    "competencies": {{
        "technical": [],
        "tools": []
    }},
    "experience": [],
    "education": []
}}

IMPORTANT:

- Do not invent information.
- Use only evidence from the resume.
- Keep technical skills and tools separate.
- Do not assign seniority without evidence.
- Prefer the candidate's demonstrated experience over speculative
  career goals.

RESUME:

{resume}
"""


# ==============================================================
# RESUME-JOB MATCH PROMPT
# ==============================================================

RESUME_JOB_MATCH_PROMPT = """
You are an expert recruitment and ATS matching system.

Compare the candidate's resume with the supplied job description.

Analyze:

- skill match
- keyword match
- experience match
- education match
- missing skills
- matching skills
- overall suitability

Return ONLY valid JSON.

Return EXACTLY:

{{
    "overall_score": 0,
    "skill_score": 0,
    "keyword_score": 0,
    "experience_score": 0,
    "education_score": 0,
    "matched_skills": [],
    "missing_skills": [],
    "suggestions": []
}}

SCORING:

All scores must be between 0 and 100.

IMPORTANT:

- Do not invent candidate skills.
- A skill is matched only when supported by the resume.
- Do not assume experience that is not present.
- Do not treat a preferred skill as mandatory.
- Keep suggestions actionable.

RESUME:

{resume}

JOB DESCRIPTION:

{job_description}
"""


# ==============================================================
# RESUME IMPROVEMENT PROMPT
# ==============================================================

RESUME_IMPROVEMENT_PROMPT = """
You are an expert resume improvement specialist and ATS consultant.

Your task is to improve the candidate's resume content while
strictly preserving factual accuracy.

IMPORTANT RULES:

1. Return ONLY valid JSON.
2. Do NOT return markdown.
3. Do NOT return code fences.
4. Do NOT include explanations outside the JSON.
5. Do NOT invent experience.
6. Do NOT invent skills.
7. Do NOT invent achievements.
8. Do NOT invent certifications.
9. Do NOT invent companies.
10. Do NOT invent education.
11. Do NOT invent projects.
12. Do NOT change dates.
13. Preserve measurable achievements.
14. Improve wording, clarity, professionalism, and ATS compatibility.
15. Use strong action verbs where appropriate.
16. Do not exaggerate the candidate's experience.

Return EXACTLY:

{{
    "improved_summary": "",
    "improved_experience": [],
    "improved_projects": [],
    "improved_skills": [],
    "ats_keywords": [],
    "improvements": []
}}

FIELD RULES:

improved_summary:
Rewrite the professional summary using only factual information
from the resume.

Maximum 100 words.

improved_experience:
Improve the wording of existing employment experience.

Do not add responsibilities that are not present.

Maximum 8 items.

improved_projects:
Improve descriptions of existing projects.

Do not invent project functionality.

Maximum 8 items.

improved_skills:
Return the candidate's existing skills in a clean,
ATS-friendly format.

Do not add unsupported skills.

Maximum 30 items.

ats_keywords:
Identify ATS keywords already supported by the resume.

Do not invent qualifications.

Maximum 20 items.

improvements:
Provide actionable recommendations for improving the resume.

Maximum 10 items.

RESUME:

{resume}
"""




# ==============================================================
# SKILL GAP PROMPT
# ==============================================================

SKILL_GAP_PROMPT = """
You are an expert career-development and skill-gap analysis system.

Compare the candidate's existing skills with the requirements of
the target role.

Return ONLY valid JSON.

Return EXACTLY:

{{
    "matched_skills": [],
    "missing_skills": [],
    "priority_skills": [],
    "recommendations": []
}}

IMPORTANT:

- Do not invent existing candidate skills.
- Missing skills must come from the target requirements.
- Prioritize skills that have the greatest impact on employability.
- Keep recommendations practical.

RESUME:

{resume}

TARGET JOB:

{job_description}
"""
