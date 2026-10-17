"""
Seniority / experience-level helpers
------------------------------------

Used to stop the analyzer from recommending the same roles to a fresher
and to an engineer with 8 years of experience.

Levels (numeric so they can be compared):

    0 = Entry Level (fresher / intern / < 1 year)
    1 = Junior      (1 - 3 years)
    2 = Mid         (3 - 6 years)
    3 = Senior      (6 - 10 years)
    4 = Lead        (10+ years, or a lead / manager / architect title)
"""

from __future__ import annotations

import re
from datetime import date
from typing import Dict, List, Optional, Tuple

LEVEL_NAMES = {
    0: "Entry Level",
    1: "Junior",
    2: "Mid-Level",
    3: "Senior",
    4: "Lead",
}

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

_PRESENT = r"(?:present|current|currently|now|till\s+date|to\s+date|ongoing)"
_MONTH = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|"
    r"july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)"
)

# "Jan 2019 - Mar 2022", "2018 - 2021", "03/2019 – Present", "Jun'19 - Present"
_RANGE_RE = re.compile(
    rf"""
    (?P<s_month>{_MONTH}|\d{{1,2}}\s*[/\-.])?\s*['’]?\.?\s*
    (?P<s_year>(?:19|20)\d{{2}}|\d{{2}}(?=\s*[-–—to]))
    \s*(?:-|–|—|to|until|till)\s*
    (?:(?P<e_month>{_MONTH}|\d{{1,2}}\s*[/\-.])?\s*['’]?\.?\s*
       (?P<e_year>(?:19|20)\d{{2}})|(?P<present>{_PRESENT}))
    """,
    re.IGNORECASE | re.VERBOSE,
)

_EXPLICIT_YEARS_RE = re.compile(
    r"(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)\b(?:\s+of)?"
    r"(?:\s+(?:total|overall|professional|relevant|industry|work|working))*"
    r"\s*(?:experience|exp)",
    re.IGNORECASE,
)

_EXPERIENCE_OF_RE = re.compile(
    r"experience\s*(?:of|:)?\s*(?:over|around|about|more than)?\s*"
    r"(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)",
    re.IGNORECASE,
)

_LEAD_TITLE_RE = re.compile(
    r"\b(principal|staff engineer|architect|engineering manager|"
    r"head of|director|vp of|tech lead|team lead|lead engineer|"
    r"lead developer)\b",
    re.IGNORECASE,
)


def _month_index(token: Optional[str], default: int) -> int:
    if not token:
        return default
    token = token.strip().lower().rstrip("/-. ")
    if token.isdigit():
        value = int(token)
        return value if 1 <= value <= 12 else default
    return _MONTHS.get(token[:3], default)


def _merge(intervals: List[Tuple[int, int]]) -> int:
    """Total months covered by (start, end) month-indexes, overlaps merged."""
    if not intervals:
        return 0
    intervals.sort()
    total = 0
    cur_s, cur_e = intervals[0]
    for s, e in intervals[1:]:
        if s <= cur_e:
            cur_e = max(cur_e, e)
        else:
            total += cur_e - cur_s
            cur_s, cur_e = s, e
    total += cur_e - cur_s
    return total


def years_from_date_ranges(text: str, today: Optional[date] = None) -> float:
    """Sum of all date ranges in the text (overlaps counted once)."""
    today = today or date.today()
    now_idx = today.year * 12 + today.month
    intervals: List[Tuple[int, int]] = []

    for m in _RANGE_RE.finditer(text or ""):
        try:
            s_year = int(m.group("s_year"))
            if s_year < 100:
                s_year += 2000 if s_year < 70 else 1900
            if not 1980 <= s_year <= today.year:
                continue
            start = s_year * 12 + _month_index(m.group("s_month"), 6)

            if m.group("present"):
                end = now_idx
            else:
                e_year = int(m.group("e_year"))
                if e_year > today.year + 1:
                    continue
                # a bare year range like "2018 - 2021" spans to year-end
                default_end = 6 if not m.group("e_month") else 1
                end = e_year * 12 + _month_index(m.group("e_month"), default_end)
                end = min(end, now_idx)
        except (TypeError, ValueError):
            continue

        if end > start and (end - start) <= 12 * 40:
            intervals.append((start, end))

    return round(_merge(intervals) / 12.0, 1)


def explicit_years(text: str) -> Optional[float]:
    """'5+ years of experience' style claims. Returns the largest sane one."""
    values = []
    for rx in (_EXPLICIT_YEARS_RE, _EXPERIENCE_OF_RE):
        for m in rx.finditer(text or ""):
            try:
                v = float(m.group(1))
            except ValueError:
                continue
            if 0 < v <= 45:
                values.append(v)
    return max(values) if values else None


def estimate_years(
    experience_text: str = "",
    full_text: str = "",
    summary: str = "",
) -> float:
    """
    Best estimate of professional experience in years.

    Priority:
      1. Date ranges found in the experience section (most reliable).
      2. An explicit "N years of experience" claim (summary / full text).
    The larger of the two is used when both exist, because resumes often
    list only recent jobs but state the total in the summary.
    """
    dated = years_from_date_ranges(experience_text or "")
    if not dated and not (experience_text or "").strip():
        # no experience section found: use dates from the rest of the resume
        dated = years_from_date_ranges(full_text or "")
    claimed = explicit_years(" ".join([summary or "", experience_text or "", full_text or ""]))

    if claimed is not None and dated:
        # trust the claim only if it is not wildly bigger than the dates
        return max(dated, min(claimed, dated + 3))
    if claimed is not None:
        return claimed
    return dated


def level_from_years(years: float) -> int:
    if years < 1:
        return 0
    if years < 3:
        return 1
    if years < 6:
        return 2
    return 3          # 6+ years; "Lead" (4) needs a lead/manager title


def candidate_level(
    years: float,
    experience_text: str = "",
    declared: str = "",
) -> int:
    """
    Candidate level from years of experience.

    Titles such as "Senior" or "Intern" only adjust the result when the
    dates are missing; years are the primary signal.
    """
    level = level_from_years(years)

    if years <= 0:
        text = f"{experience_text} {declared}".lower()
        if _LEAD_TITLE_RE.search(text):
            level = 4
        elif re.search(r"\bsenior\b|\bsr\.?\b", text):
            level = 3
        elif re.search(r"\b(junior|jr\.?|associate)\b", text):
            level = 1
        else:
            level = 0
    elif years >= 6 and _LEAD_TITLE_RE.search(experience_text or ""):
        level = max(level, 4)

    return level


# ----------------------------------------------------------------------
# Job side
# ----------------------------------------------------------------------

_JOB_TITLE_PATTERNS = [
    (4, re.compile(r"\b(principal|staff|architect|director|head|vp|"
                   r"engineering manager|lead|manager)\b", re.I)),
    (3, re.compile(r"\b(senior|sr\.?|iii|iv)\b", re.I)),
    (0, re.compile(r"\b(intern|internship|trainee|fresher|graduate|"
                   r"apprentice|entry[\s-]?level)\b", re.I)),
    (1, re.compile(r"\b(junior|jr\.?|associate|i\b|level\s*1)\b", re.I)),
    (2, re.compile(r"\b(ii|mid[\s-]?level|level\s*2)\b", re.I)),
]

_REQ_YEARS_RE = re.compile(
    r"(\d{1,2})\s*(?:\+|-|–|to)?\s*(?:\d{1,2})?\s*\+?\s*(?:years?|yrs?)"
    r"\s*(?:of\s*)?(?:relevant\s*|professional\s*|hands[\s-]on\s*)?"
    r"(?:experience|exp)",
    re.IGNORECASE,
)


def job_level_from_title(title: str) -> Optional[int]:
    for level, rx in _JOB_TITLE_PATTERNS:
        if rx.search(title or ""):
            return level
    return None


def required_years(description: str) -> Optional[int]:
    """Smallest 'N years experience' requirement mentioned in a job post."""
    values = []
    for m in _REQ_YEARS_RE.finditer(description or ""):
        try:
            v = int(m.group(1))
        except ValueError:
            continue
        if 0 <= v <= 30:
            values.append(v)
    return min(values) if values else None


def job_level(title: str, description: str = "") -> Optional[int]:
    """Level a job is aimed at, from its title first, then required years."""
    lvl = job_level_from_title(title)
    if lvl is not None:
        return lvl
    req = required_years(description)
    if req is not None:
        return level_from_years(float(req))
    return None


def level_fit(
    cand_level: int,
    cand_years: float,
    title: str,
    description: str = "",
) -> Dict[str, object]:
    """
    How well a job's level fits the candidate.

    Returns {"multiplier": 0..1, "exclude": bool, "note": str}
    """
    lvl = job_level(title, description)
    req = required_years(description)

    if lvl is None:
        return {"multiplier": 1.0, "exclude": False, "note": ""}

    diff = lvl - cand_level

    # Too senior for the candidate
    if diff >= 2 or (req is not None and req >= cand_years + 3):
        return {
            "multiplier": 0.0,
            "exclude": True,
            "note": f"Requires more experience than you have "
                    f"({LEVEL_NAMES.get(lvl, '')} role).",
        }
    if diff == 1 or (req is not None and req > cand_years + 1.5):
        return {
            "multiplier": 0.6,
            "exclude": False,
            "note": "Stretch role: slightly above your current level.",
        }

    # Too junior for the candidate (e.g. 8-year engineer shown an internship)
    if diff <= -2:
        return {
            "multiplier": 0.0,
            "exclude": True,
            "note": f"Below your experience level ({LEVEL_NAMES.get(lvl, '')} role).",
        }
    if diff == -1:
        return {
            "multiplier": 0.8,
            "exclude": False,
            "note": "Slightly below your current level.",
        }

    return {
        "multiplier": 1.0,
        "exclude": False,
        "note": f"Matches your level ({LEVEL_NAMES.get(cand_level, '')}).",
    }


def search_level_keyword(level: int) -> str:
    """Word added to job-search queries so results come back level-appropriate."""
    return {0: "fresher", 1: "junior", 2: "", 3: "senior", 4: "lead"}.get(level, "")


def apply_seniority(resume, full_text: str = "", experience_text=None) -> None:
    """
    Compute experience years / level for a parsed Resume and store them on it
    (also overwrites the weak keyword-based career_profile.seniority).

    experience_text: dates must come from the ORIGINAL resume text. When it is
    given, the AI-written resume.experience is ignored for the years
    calculation (AI output can contain invented dates).
    """
    exp_text = (
        experience_text
        if experience_text is not None
        else (getattr(resume, "experience", "") or "")
    )

    years = estimate_years(
        experience_text=exp_text,
        full_text=full_text or "",
        summary="",
    )
    profile = getattr(resume, "career_profile", None)
    declared = getattr(profile, "seniority", "") if profile else ""
    level = candidate_level(
        years,
        experience_text=exp_text,
        declared="",
    )
    resume.experience_years = years
    resume.experience_level = level
    if profile is not None:
        profile.seniority = LEVEL_NAMES[level]


def get_level(resume) -> Tuple[int, float]:
    """(level, years) for a resume, computing it if needed."""
    if not getattr(resume, "experience_years", 0) and not getattr(resume, "experience_level", 0):
        apply_seniority(resume)
    return int(getattr(resume, "experience_level", 0)), float(getattr(resume, "experience_years", 0.0))
