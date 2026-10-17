"""
Resume Parser
=============

Parses PDF/DOCX resumes into the Resume model.

Pipeline:

    Resume File
        ↓
    FileReaderFactory
        ↓
    Raw Text
        ↓
    Text Cleaning
        ↓
    AI Extraction
        ↓
    Resume Model

If AI parsing fails, a deterministic local parser is used.
This prevents resume analysis from completely failing because
of temporary AI provider problems.
"""

from __future__ import annotations

import copy
import hashlib
import logging
import os
import re
import threading
from typing import Any, Dict, List

from app.core.config import RESUME_PARSER_MAX_TOKENS, AI_PARSE_BUDGET_SECONDS
from app.models.resume import Resume
from app.parser.sections import sanitize_text, split_sections
from app.utils.seniority import apply_seniority
from app.services.ai_service import AIService
from app.readers.factory import FileReaderFactory
from app.exceptions.custom_exceptions import (
    AIServiceError,
    ResumeParserError,
)


logger = logging.getLogger("ResumeAnalyzer")


class ResumeParser:

    def __init__(
        self,
        development_mode: bool = False,
    ):

        self.development_mode = development_mode
        self.ai_service = AIService()

        logger.info(
            "ResumeParser initialized. Development mode: %s",
            self.development_mode,
        )

    # ==========================================================
    # TEXT CLEANING
    # ==========================================================

    @staticmethod
    def _clean_text(
        text: str,
    ) -> str:

        if not isinstance(text, str):
            return ""

        text = sanitize_text(text)

        text = text.replace(
            "\r\n",
            "\n",
        )

        text = text.replace(
            "\r",
            "\n",
        )

        text = text.replace(
            "\x00",
            "",
        )

        cleaned_lines = []

        for line in text.split("\n"):

            line = " ".join(
                line.split()
            )

            if line:
                cleaned_lines.append(
                    line
                )

        return "\n".join(
            cleaned_lines
        )

    # ==========================================================
    # NORMALIZATION HELPERS
    # ==========================================================

    @staticmethod
    def _clean_list(
        value: Any,
    ) -> List[str]:

        if value is None:
            return []

        if isinstance(
            value,
            str,
        ):

            value = [
                value
            ]

        if not isinstance(
            value,
            list,
        ):
            return []

        result = []

        for item in value:

            if isinstance(
                item,
                dict,
            ):

                item = (
                    item.get("name")
                    or item.get("skill")
                    or item.get("title")
                    or item.get("text")
                    or ""
                )

            item = str(
                item
            ).strip()

            if item:
                result.append(
                    item
                )

        return list(
            dict.fromkeys(
                result
            )
        )

    # ==========================================================
    # EMAIL
    # ==========================================================

    @staticmethod
    def _extract_email(
        text: str,
    ) -> str:

        match = re.search(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            text,
        )

        return (
            match.group(0)
            if match
            else ""
        )

    # ==========================================================
    # PHONE
    # ==========================================================

    @staticmethod
    def _extract_phone(
        text: str,
    ) -> str:

        patterns = [
            r"(?:\+91[\s-]?)?[6-9]\d{9}",
            r"(?:\+?\d{1,3}[\s-]?)?\d{10}",
            r"\+?\d[\d\s().-]{8,}\d",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
            )

            if match:

                phone = (
                    match.group(0)
                    .strip()
                )

                phone = re.sub(
                    r"\s+",
                    " ",
                    phone,
                )

                return phone

        return ""

    # ==========================================================
    # NAME
    # ==========================================================

    @staticmethod
    def _extract_name(
        text: str,
        email: str,
    ) -> str:

        lines = [
            line.strip()
            for line in text.split("\n")
            if line.strip()
        ]

        if not lines:
            return ""

        contact_words = re.compile(
            r"phone|mobile|email|e-mail|linkedin|github|portfolio|address|"
            r"marker|envelope|india|resume|curriculum|vitae|profile|summary|"
            r"objective|experience|education|skills|projects|contact|"
            r"http|www|\.com|\+\d",
            re.IGNORECASE,
        )

        def looks_like_name(line: str) -> bool:
            if contact_words.search(line) or re.search(r"\d", line):
                return False
            words = line.replace(",", " ").split()
            if not 2 <= len(words) <= 4:
                return False
            return all(
                re.match(r"^[A-Za-z][A-Za-z.'-]*$", w)
                and (w[0].isupper() or w.isupper())
                for w in words
            )

        for line in lines[:15]:
            if looks_like_name(line):
                return line.title() if line.isupper() else line

        # "Sanskar Sinha  +91 98756 43914  name@mail.com" - the name is
        # whatever comes before the first phone number / e-mail / separator.
        for line in lines[:6]:
            head = re.split(r"[\d@|•·●▪,]|\+|https?:|www\.|\s{3,}", line, maxsplit=1)[0].strip(" -–—:/")
            if head and head != line and looks_like_name(head):
                return head.title() if head.isupper() else head

        # Name directly above the e-mail line.
        if email:
            before = text.split(email, 1)[0].split("\n")
            for line in reversed([l.strip() for l in before if l.strip()][-5:]):
                if looks_like_name(line):
                    return line.title() if line.isupper() else line

        # Name from the e-mail address (jane.doe@x.com -> Jane Doe).
        if email and "@" in email:
            local = re.sub(r"\d+", " ", email.split("@")[0])
            parts = [p for p in re.split(r"[._\-\s]+", local) if len(p) > 1]
            if 1 <= len(parts) <= 3:
                return " ".join(p.capitalize() for p in parts)

        return ""

    # ==========================================================
    # SECTION EXTRACTION
    # ==========================================================

    @staticmethod
    def _extract_section(
        text: str,
        headings: List[str],
    ) -> str:

        lines = text.split("\n")

        heading_pattern = re.compile(
            r"^\s*(?:"
            + "|".join(
                re.escape(h)
                for h in headings
            )
            + r")\s*:?\s*$",
            re.IGNORECASE,
        )

        start_index = None

        for index, line in enumerate(lines):

            if heading_pattern.match(
                line
            ):

                start_index = index + 1
                break

        if start_index is None:
            return ""

        next_headings = [
            "summary",
            "objective",
            "skills",
            "technical skills",
            "experience",
            "work experience",
            "professional experience",
            "education",
            "projects",
            "certifications",
            "achievements",
            "contact",
            "profile",
        ]

        output = []

        for line in lines[start_index:]:

            stripped = line.strip()

            if not stripped:
                continue

            if any(
                re.match(
                    rf"^\s*{re.escape(h)}\s*:?\s*$",
                    stripped,
                    re.IGNORECASE,
                )
                for h in next_headings
            ):
                break

            output.append(
                stripped
            )

        return "\n".join(
            output
        )

    # ==========================================================
    # SKILL EXTRACTION
    # ==========================================================

    @classmethod
    def _extract_skills(
        cls,
        text: str,
    ) -> List[str]:

        section = split_sections(text).get("skills", "")

        if not section:
            section = cls._extract_section(
                text,
                [
                    "skills",
                    "technical skills",
                    "technical skill",
                    "key skills",
                    "core skills",
                    "skills & technologies",
                    "technologies",
                ],
            )

        source = section or text

        known_skills = [
            "Python", "Java", "C", "C++", "C#", "Go", "Rust", "PHP", "Ruby",
            "Kotlin", "Swift", "R", "Scala", "JavaScript", "TypeScript",
            "HTML", "CSS", "React", "Angular", "Vue", "Next.js", "Node.js",
            "Express", "FastAPI", "Django", "Flask", "Spring Boot", ".NET",
            "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "Oracle",
            "SQLite", "Power BI", "Tableau", "Excel", "Git", "GitHub",
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Linux",
            "Terraform", "Jenkins", "CI/CD", "REST API", "GraphQL",
            "Microservices", "Kafka", "Airflow", "Machine Learning",
            "Deep Learning", "NLP", "LLM", "TensorFlow", "PyTorch", "Keras",
            "Pandas", "NumPy", "Scikit-learn", "Spark", "PySpark",
            "Databricks", "Hadoop", "ETL", "Data Analysis", "Data Analytics",
            "Statistics", "Cyber Security", "Cybersecurity", "Networking",
            "Cisco", "Wireshark", "Burp Suite", "PowerShell", "Bash",
            "Figma", "Jira", "Selenium", "Android", "Flutter",
            "React Native", "Agile", "Scrum", "Salesforce", "SAP",
        ]

        found = []
        seen = set()

        def add(skill: str) -> None:
            key = skill.lower()
            if key not in seen:
                seen.add(key)
                found.append(skill)

        for skill in known_skills:

            # whole-word match: "C" must not match "Computer", "Java"
            # must not match "JavaScript", "R" must not match "React".
            pattern = (
                r"(?<![A-Za-z0-9+#.])"
                + re.escape(skill)
                + r"(?![A-Za-z0-9+#])"
            )

            if re.search(pattern, source, re.IGNORECASE if len(skill) > 2 else 0):
                add(skill)

        # Extra items listed in the skills section itself.
        if section:

            for line in section.split("\n"):

                # "Programming Languages: Python, C" -> "Python, C"
                line = re.sub(r"^[A-Za-z &/]{3,30}:\s*", "", line)

                for chunk in re.split(r"[,|•·;]", line):

                    cleaned = chunk.strip(" -:\t●◦▪")

                    if (
                        cleaned
                        and 2 <= len(cleaned) <= 40
                        and len(cleaned.split()) <= 4
                        and not re.search(r"[.!?]$", cleaned)
                    ):
                        add(cleaned)

        return found[:50]

    # ==========================================================
    # EDUCATION
    # ==========================================================

    @classmethod
    def _extract_education(
        cls,
        text: str,
    ) -> List[str]:

        section = cls._extract_section(
            text,
            [
                "education",
                "academic background",
                "educational qualification",
                "qualifications",
            ],
        )

        if not section:
            return []

        lines = [
            line.strip()
            for line in section.split("\n")
            if line.strip()
        ]

        return lines[:15]

    # ==========================================================
    # PROJECTS
    # ==========================================================

    @classmethod
    def _extract_projects(
        cls,
        text: str,
    ) -> List[str]:

        section = split_sections(text).get("projects", "")

        if not section:
            section = cls._extract_section(
                text,
                [
                    "projects",
                    "academic projects",
                    "personal projects",
                    "key projects",
                ],
            )

        if not section:
            return []

        projects = []

        for line in section.split("\n"):

            cleaned = re.sub(
                r"^[•●◦▪\-\*\d.)\s]+",
                "",
                line.strip(),
            ).strip()

            if not cleaned:
                continue

            # Keep project titles, not every description bullet:
            # a title is short, or ends before a ':' / ' - ' / '|'.
            title = re.split(r"\s[-–—|:]\s|:\s", cleaned, maxsplit=1)[0].strip()

            is_bullet = bool(re.match(r"^[•●◦▪\-\*]", line.strip()))

            if is_bullet and len(cleaned.split()) > 12:
                continue                      # description sentence

            if len(title.split()) <= 10 and title not in projects:
                projects.append(title)

        return projects[:10]

    # ==========================================================
    # EXPERIENCE
    # ==========================================================

    @classmethod
    def _extract_experience(
        cls,
        text: str,
    ) -> str:

        sections = split_sections(text)

        found = sections.get("experience", "").strip()

        if found:
            return found

        # Old exact-heading approach as a second chance.
        return cls._extract_section(
            text,
            [
                "experience",
                "work experience",
                "professional experience",
                "employment",
                "internship",
            ],
        ).strip()

    # ==========================================================
    # SUMMARY
    # ==========================================================

    @classmethod
    def _extract_summary(
        cls,
        text: str,
    ) -> str:

        section = cls._extract_section(
            text,
            [
                "summary",
                "professional summary",
                "profile",
                "objective",
                "career objective",
            ],
        )

        if section:
            return section[:1500]

        return ""

    # ==========================================================
    # CAREER PROFILE
    # ==========================================================

    @classmethod
    def _build_career_profile(
        cls,
        text: str,
        skills: List[str],
        experience: str,
        education: List[str],
    ) -> Dict[str, Any]:

        lower = text.lower()

        role = ""

        role_patterns = [
            (
                r"\bdata analyst\b",
                "Data Analyst",
            ),
            (
                r"\bbusiness data analyst\b",
                "Business Data Analyst",
            ),
            (
                r"\bdata engineer\b",
                "Data Engineer",
            ),
            (
                r"\bsoftware engineer\b",
                "Software Engineer",
            ),
            (
                r"\bsoftware developer\b",
                "Software Developer",
            ),
            (
                r"\bbackend engineer\b",
                "Backend Engineer",
            ),
            (
                r"\bpython developer\b",
                "Python Developer",
            ),
            (
                r"\bweb developer\b",
                "Web Developer",
            ),
            (
                r"\bcyber security\b",
                "Cyber Security",
            ),
            (
                r"\bcybersecurity\b",
                "Cybersecurity",
            ),
            (
                r"\bmachine learning\b",
                "Machine Learning Engineer",
            ),
        ]

        for pattern, value in role_patterns:

            if re.search(
                pattern,
                lower,
            ):
                role = value
                break

        profession = ""

        if any(
            x in lower
            for x in [
                "data analyst",
                "data engineer",
                "data science",
            ]
        ):
            profession = "Data"

        elif any(
            x in lower
            for x in [
                "software engineer",
                "software developer",
                "backend",
                "frontend",
                "full stack",
            ]
        ):
            profession = "Technology"

        elif any(
            x in lower
            for x in [
                "cyber security",
                "cybersecurity",
            ]
        ):
            profession = "Cyber Security"

        industry = ""

        if "bank" in lower or "finance" in lower:
            industry = "Finance"

        elif "healthcare" in lower:
            industry = "Healthcare"

        elif (
            "software" in lower
            or "technology" in lower
            or "it industry" in lower
        ):
            industry = "Software"

        seniority = ""

        if re.search(
            r"\b(intern|internship|fresher|student)\b",
            lower,
        ):
            seniority = "Entry Level"

        elif re.search(
            r"\b(senior|lead|manager)\b",
            lower,
        ):
            seniority = "Senior"

        elif re.search(
            r"\b(junior|associate)\b",
            lower,
        ):
            seniority = "Junior"

        technical = []
        tools = []

        technical_keywords = {
            "Python",
            "Java",
            "C",
            "C++",
            "JavaScript",
            "SQL",
            "FastAPI",
            "Django",
            "React",
            "REST API",
            "Machine Learning",
            "Deep Learning",
            "NLP",
            "TensorFlow",
            "PyTorch",
            "Pandas",
            "NumPy",
            "PySpark",
            "Spark",
            "ETL",
            "Data Analysis",
            "Cyber Security",
        }

        tool_keywords = {
            "Git",
            "GitHub",
            "Docker",
            "AWS",
            "Azure",
            "GCP",
            "MySQL",
            "PostgreSQL",
            "MongoDB",
            "Power BI",
            "Tableau",
            "Excel",
            "Linux",
            "Windows",
            "Databricks",
            "Cisco",
            "Wireshark",
            "Burp Suite",
        }

        for skill in skills:

            if skill in technical_keywords:
                technical.append(skill)

            elif skill in tool_keywords:
                tools.append(skill)

        return {
            "profession": profession,
            "role": role,
            "industry": industry,
            "seniority": seniority,
            "competencies": {
                "technical": technical,
                "tools": tools,
            },
            "experience": [],
            "education": [],
        }

    # ==========================================================
    # LOCAL FALLBACK
    # ==========================================================

    @classmethod
    def _fallback_parse(
        cls,
        text: str,
    ) -> Dict[str, Any]:

        logger.warning(
            "Using deterministic local resume parser fallback."
        )

        email = cls._extract_email(
            text
        )

        phone = cls._extract_phone(
            text
        )

        name = cls._extract_name(
            text,
            email,
        )

        skills = cls._extract_skills(
            text
        )

        education = cls._extract_education(
            text
        )

        projects = cls._extract_projects(
            text
        )

        experience = cls._extract_experience(
            text
        )

        summary = cls._extract_summary(
            text
        )

        career_profile = cls._build_career_profile(
            text,
            skills,
            experience,
            education,
        )

        if not summary:

            if career_profile.get(
                "role"
            ):

                summary = (
                    f"Candidate with skills in "
                    f"{', '.join(skills[:8])}."
                )

            else:

                summary = (
                    "Candidate with technical and "
                    "professional skills presented in "
                    "the resume."
                )

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "skills": skills,
            "experience": experience,
            "education": education,
            "projects": projects,
            "resume_score": 0,
            "summary": summary,
            "career_profile": career_profile,
        }

    # ==========================================================
    # NORMALIZE AI DATA
    # ==========================================================

    @classmethod
    def _normalize_ai_data(
        cls,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not isinstance(
            data,
            dict,
        ):
            raise ResumeParserError(
                "AI did not return a valid resume object."
            )

        normalized = {
            "name": str(
                data.get(
                    "name",
                    "",
                )
                or ""
            ).strip(),

            "email": str(
                data.get(
                    "email",
                    "",
                )
                or ""
            ).strip(),

            "phone": str(
                data.get(
                    "phone",
                    "",
                )
                or ""
            ).strip(),

            "skills": cls._clean_list(
                data.get(
                    "skills",
                    [],
                )
            ),

            "experience": str(
                data.get(
                    "experience",
                    "",
                )
                or ""
            ).strip(),

            "education": cls._clean_list(
                data.get(
                    "education",
                    [],
                )
            ),

            "projects": cls._clean_list(
                data.get(
                    "projects",
                    [],
                )
            ),

            "resume_score": 0,

            "summary": str(
                data.get(
                    "summary",
                    "",
                )
                or ""
            ).strip(),
        }

        career = data.get(
            "career_profile",
            {},
        )

        if not isinstance(
            career,
            dict,
        ):
            career = {}

        competencies = career.get(
            "competencies",
            {},
        )

        if not isinstance(
            competencies,
            dict,
        ):
            competencies = {}

        normalized["career_profile"] = {
            "profession": str(
                career.get(
                    "profession",
                    "",
                )
                or ""
            ).strip(),

            "role": str(
                career.get(
                    "role",
                    "",
                )
                or ""
            ).strip(),

            "industry": str(
                career.get(
                    "industry",
                    "",
                )
                or ""
            ).strip(),

            "seniority": str(
                career.get(
                    "seniority",
                    "",
                )
                or ""
            ).strip(),

            "competencies": {
                "technical": cls._clean_list(
                    competencies.get(
                        "technical",
                        [],
                    )
                ),
                "tools": cls._clean_list(
                    competencies.get(
                        "tools",
                        [],
                    )
                ),
            },

            "experience": [],

            "education": [],
        }

        return normalized

    # ==========================================================
    # PARSE
    # ==========================================================

    # ==========================================================
    # MERGE AI RESULT INTO LOCAL RESULT
    # ==========================================================

    @classmethod
    def _merge_ai_into_local(
        cls,
        local: Dict[str, Any],
        ai: Dict[str, Any],
        text: str,
    ) -> Dict[str, Any]:
        """
        AI output refines the local parse. The local parse fills every gap,
        so experience / projects can no longer silently come back empty.
        """

        if not isinstance(ai, dict):
            return local

        merged = dict(local)

        def as_text(value) -> str:
            if isinstance(value, list):
                return "\n".join(
                    ", ".join(str(x) for x in v.values() if x)
                    if isinstance(v, dict) else str(v)
                    for v in value
                )
            if isinstance(value, dict):
                return ", ".join(str(x) for x in value.values() if x)
            return str(value or "").strip()

        def as_list(value) -> List[str]:
            if isinstance(value, str):
                value = [value]
            if not isinstance(value, list):
                return []
            out = []
            for item in value:
                if isinstance(item, dict):
                    item = ", ".join(str(x) for x in item.values() if x)
                item = str(item or "").strip()
                if item and item not in out:
                    out.append(item)
            return out

        name = as_text(ai.get("name"))
        if (
            name
            and 2 <= len(name.split()) <= 4
            and not re.search(r"\d|@", name)
            and sanitize_text(name) == name
        ):
            merged["name"] = name

        ai_skills = as_list(ai.get("skills"))
        if ai_skills:
            seen = set()
            skills = []
            for skill in ai_skills + list(local.get("skills") or []):
                key = skill.lower()
                if key not in seen:
                    seen.add(key)
                    skills.append(skill)
            merged["skills"] = skills[:40]

        ai_experience = as_text(ai.get("experience"))
        local_experience = local.get("experience", "") or ""
        if len(ai_experience) >= 20:
            # keep the original lines too: they carry the dates
            merged["experience"] = (
                ai_experience
                if not local_experience
                else ai_experience + "\n" + local_experience
            )
        else:
            merged["experience"] = local_experience

        education = as_list(ai.get("education"))
        if education:
            merged["education"] = education

        projects = as_list(ai.get("projects"))
        if projects:
            seen_p = {x.lower() for x in projects}
            projects += [
                x for x in (local.get("projects") or [])
                if x.lower() not in seen_p
            ]
            merged["projects"] = projects[:10]

        summary = as_text(ai.get("summary"))
        if summary:
            merged["summary"] = summary

        role = as_text(ai.get("role"))
        if role and isinstance(merged.get("career_profile"), dict):
            merged["career_profile"]["role"] = role

        return merged

    # Parsed resumes are cached by file-content hash, with a per-file lock,
    # so the same resume is never sent to the AI twice (even when two
    # requests for it arrive at the same moment).
    _CACHE: Dict[str, Resume] = {}
    _LOCKS: Dict[str, threading.Lock] = {}
    _GUARD = threading.Lock()
    _CACHE_MAX = 64

    def parse(
        self,
        file_path,
    ) -> Resume:

        key = None

        try:
            if isinstance(file_path, str) and os.path.isfile(file_path.strip()):
                with open(file_path.strip(), "rb") as handle:
                    key = hashlib.sha256(handle.read()).hexdigest()
        except OSError:
            key = None

        if not key:
            return self._parse_uncached(file_path)

        with self._GUARD:
            lock = self._LOCKS.setdefault(key, threading.Lock())

        with lock:

            if key in self._CACHE:
                logger.info("Resume parse cache hit.")
                return copy.deepcopy(self._CACHE[key])

            resume = self._parse_uncached(file_path)

            with self._GUARD:
                if len(self._CACHE) >= self._CACHE_MAX:
                    self._CACHE.pop(next(iter(self._CACHE)))
                self._CACHE[key] = copy.deepcopy(resume)

            return resume

    def _parse_uncached(
        self,
        file_path,
    ) -> Resume:

        logger.info(
            "Parsing resume %s",
            file_path,
        )

        if not isinstance(
            file_path,
            str,
        ):
            raise ResumeParserError(
                "Resume path must be a string."
            )

        file_path = file_path.strip()

        if not file_path:
            raise ResumeParserError(
                "Resume path cannot be empty."
            )

        if file_path.lower() == "string":
            raise ResumeParserError(
                "Invalid resume path: 'string'."
            )

        if not os.path.isfile(
            file_path
        ):
            raise ResumeParserError(
                f"Resume file does not exist: {file_path}"
            )

        # ------------------------------------------------------
        # Read file
        # ------------------------------------------------------

        try:

            reader = FileReaderFactory.get_reader(
                file_path
            )

            raw_text = reader.read(
                file_path
            )

        except Exception as error:

            logger.exception(
                "Failed to extract resume text."
            )

            raise ResumeParserError(
                f"Failed to read resume: {error}"
            ) from error

        text = self._clean_text(
            raw_text
        )

        if not text:
            raise ResumeParserError(
                "Resume contains no readable text."
            )

        logger.info(
            "Clean resume text length: %s",
            len(text),
        )

        # ------------------------------------------------------
        # Development mode
        # ------------------------------------------------------

        if self.development_mode:

            return Resume.from_dict(
                {
                    "name": "Development User",
                    "email": "development@example.com",
                    "phone": "0000000000",
                    "skills": [
                        "Python",
                        "FastAPI",
                        "Git",
                    ],
                    "experience": (
                        "Software development experience"
                    ),
                    "education": [
                        "Bachelor of Technology",
                    ],
                    "projects": [
                        "AI Resume Analyzer",
                    ],
                    "resume_score": 0,
                    "summary": (
                        "Development-mode mock resume."
                    ),
                    "career_profile": {
                        "profession": "Technology",
                        "role": "Software Engineer",
                        "industry": "Software",
                        "seniority": "Junior",
                        "competencies": {
                            "technical": [
                                "Python",
                                "FastAPI",
                            ],
                            "tools": [
                                "Git",
                            ],
                        },
                        "experience": [],
                        "education": [],
                    },
                }
            )

        # ------------------------------------------------------
        # 1. Local parse first: instant, never fails.
        # ------------------------------------------------------

        data = self._fallback_parse(
            text
        )

        _sections = split_sections(text)

        # Dates for the years-of-experience calculation come from the
        # ORIGINAL text (never from AI output, which can invent dates).
        work_text = _sections.get("experience", "")

        non_education_text = "\n".join(
            part
            for kind, part in _sections.items()
            if kind in ("header", "summary", "other")
        )

        # ------------------------------------------------------
        # 2. AI refinement under a hard time budget.
        #    If the AI is slow or fails, the local result is used.
        # ------------------------------------------------------

        prompt = f"""Extract resume data as ONE JSON object. Use only facts in the resume.

{{"name":"","skills":[],"role":"",
"experience":"one line per job or internship: Title, Company, Start - End (keep the dates)",
"education":["Degree, Institution, Years"],
"projects":["project names only"],
"summary":"one sentence"}}

Rules: skills = technical skills only (max 30). Include internships under experience.
Projects are NOT employment. Do not invent anything.

RESUME:
{text[:9000]}"""

        try:

            ai_data = self.ai_service.send_json_prompt(
                prompt,
                max_tokens=900,
                temperature=0.1,
                budget=AI_PARSE_BUDGET_SECONDS,
            )

            data = self._merge_ai_into_local(
                data,
                ai_data,
                text,
            )

        except Exception as error:

            logger.warning(
                "AI resume parsing unavailable, using local parse: %s",
                error,
            )

        # ------------------------------------------------------
        # Always force resume score to zero.
        # ATS scoring is handled elsewhere.
        # ------------------------------------------------------

        data["resume_score"] = 0

        # ------------------------------------------------------
        # Create model
        # ------------------------------------------------------

        try:

            resume = Resume.from_dict(
                data
            )

        except Exception as error:

            logger.exception(
                "Failed to create Resume model."
            )

            # Try local fallback one more time.
            fallback_data = self._fallback_parse(
                text
            )

            try:

                resume = Resume.from_dict(
                    fallback_data
                )

            except Exception as fallback_error:

                raise ResumeParserError(
                    "Failed to create Resume model: "
                    f"{fallback_error}"
                ) from error

        try:
            # Years of experience come from the dates in the resume text,
            # not from the AI's guess.
            apply_seniority(
                resume,
                full_text=non_education_text,
                experience_text=work_text,
            )
        except Exception:
            logger.exception("Seniority detection failed.")

        logger.info(
            "Resume parsed (experience: %s years, level: %s).",
            getattr(resume, "experience_years", "?"),
            getattr(resume, "experience_level", "?"),
        )

        return resume