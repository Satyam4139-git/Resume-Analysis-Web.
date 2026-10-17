"""
Robust resume section splitting + text sanitising.

Real resumes use headings like "WORK EXPERIENCE", "Internships & Training",
"Academic Projects", "━━ PROJECTS ━━" ... The old parser only matched a few
exact words, so experience and projects often came back empty.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Tuple

# Order matters: "Academic Projects" must be a project, not education.
_KINDS: List[Tuple[str, re.Pattern]] = [
    ("projects", re.compile(r"\bprojects?\b|\bcapstone\b|\bportfolio\b", re.I)),
    ("experience", re.compile(
        r"\bexperience\b|\binternships?\b|\bemployment\b|\bwork\s+history\b|"
        r"\bcareer\s+history\b|\bprofessional\s+background\b|\bwork\s+summary\b|"
        r"\bindustrial\s+training\b|\btraineeship\b|\bapprenticeship\b|\bpositions?\s+held\b", re.I)),
    ("education", re.compile(r"\beducation\b|\bacademics?\b|\bqualifications?\b|\bscholastic\b", re.I)),
    ("skills", re.compile(r"\bskills?\b|\btechnolog(?:y|ies)\b|\bcompetenc|\btech\s+stack\b|\btools\b", re.I)),
    ("certifications", re.compile(r"\bcertifications?\b|\bcertificates?\b|\bcourses?\b|\blicen[cs]es?\b", re.I)),
    ("achievements", re.compile(r"\bachievements?\b|\bawards?\b|\bhonou?rs?\b|\baccomplishments?\b", re.I)),
    ("summary", re.compile(r"\bsummary\b|\bobjective\b|\bprofile\b|\babout\s+me\b|\bcareer\s+objective\b", re.I)),
    ("other", re.compile(
        r"\blanguages?\b|\bhobbies\b|\binterests?\b|\bdeclaration\b|\breferences?\b|"
        r"\bpersonal\s+(?:details|information)\b|\bpublications?\b|\bvolunteer|"
        r"\bextra[\s-]?curricular\b|\bactivities\b|\bcontact\b|\bleadership\b|\bresponsibilit", re.I)),
]


def sanitize_text(text: str) -> str:
    """
    Remove icon glyphs / private-use characters that PDF fonts inject
    (they turned names into things like 'ꢗap-Ꭷarker India').
    """
    if not isinstance(text, str):
        return ""

    out = []
    for ch in text:
        if ch in "\n\t":
            out.append(ch)
            continue
        cat = unicodedata.category(ch)
        if cat in ("Co", "Cs", "Cn", "Cf", "Cc"):
            out.append(" ")
            continue
        if cat == "So" and ch not in "•●◦▪■□★☆→–—":
            out.append(" ")        # emoji / icon symbols
            continue
        if cat.startswith("L") and ord(ch) > 0x024F and not (0x0900 <= ord(ch) <= 0x097F):
            # letters from scripts that resumes only contain as icon-font junk
            # (keep basic Latin / extended Latin / Devanagari)
            out.append(" ")
            continue
        out.append(ch)
    return "".join(out)


def _heading_kind(line: str) -> str:
    """Return the section kind if the line looks like a heading, else ''."""
    raw = line.strip()
    if not raw or len(raw) > 60:
        return ""

    letters = re.sub(r"[^A-Za-z& /,-]", " ", raw)
    words = [w for w in letters.split() if w not in ("&", "/", "-", ",")]

    if not words or len(words) > 6:
        return ""
    if "@" in raw or re.search(r"\d{4}", raw):      # dates / contact lines
        return ""
    if raw.endswith(".") or raw.endswith(","):
        return ""

    shouty = raw.upper() == raw
    colon = raw.rstrip().endswith(":")
    short = len(words) <= 3

    # Titles like "Experience", "Work Experience", "PROJECTS", "Skills:" ...
    if not (shouty or colon or short or raw.istitle()):
        return ""

    for kind, pattern in _KINDS:
        if pattern.search(letters):
            if shouty or colon:
                return kind
            # Mixed-case lines are only headings when very short, so a
            # project called "Resume Analyzer Project" is not mistaken for one.
            limit = 2 if kind == "projects" else 3
            return kind if len(words) <= limit else ""

    # Unknown but clearly a heading (ALL CAPS, short): ends the previous section.
    if shouty and len(words) <= 4 and any(len(w) > 3 for w in words):
        return "other"

    return ""


def split_sections(text: str) -> Dict[str, str]:
    """Split resume text into {kind: combined_text}."""
    sections: Dict[str, List[str]] = {}
    current = "header"

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        kind = _heading_kind(stripped)
        if kind:
            current = kind
            continue
        sections.setdefault(current, []).append(stripped)

    return {kind: "\n".join(lines) for kind, lines in sections.items()}
