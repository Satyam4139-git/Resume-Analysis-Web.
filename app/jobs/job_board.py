"""
Public job-board search (powers GET /jobs/search).

Sources
-------
* Adzuna  - ADZUNA_APP_ID + ADZUNA_APP_KEY
* Jooble  - JOOBLE_API_KEY   (optional; switches on when the key exists)

Both are queried in parallel, merged, de-duplicated, filtered by experience
level / remote, ranked, and returned in the shape the frontend (jobs.js)
expects.
"""

from __future__ import annotations

import hashlib
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

import requests

from app.core.config import (
    ADZUNA_APP_ID,
    ADZUNA_APP_KEY,
    ADZUNA_COUNTRY,
    ADZUNA_COUNTRIES,
    JOOBLE_API_KEY,
)
from app.core.logger import logger
from app.utils.seniority import job_level, required_years

REQUEST_TIMEOUT = 8          # seconds per provider (the page gives up at 15)
CACHE_TTL = 600              # 10 minutes
CACHE_MAX = 500

# How many Adzuna countries one search may query (each is one API call).
# More countries = more openings, but uses more of the free daily quota.
MAX_COUNTRIES = max(1, int(os.getenv("JOB_MAX_COUNTRIES", "3")))

LEVEL_NAMES = {0: "fresher", 1: "junior", 2: "mid", 3: "senior", 4: "senior"}
VALID_LEVELS = {"fresher", "junior", "mid", "senior"}

REMOTE_RE = re.compile(r"\bremote\b|work from home|\bwfh\b|work-from-home", re.I)
TAG_RE = re.compile(r"<[^>]+>")

SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
    "PHP", "Ruby", "Kotlin", "Swift", "SQL", "MySQL", "PostgreSQL", "MongoDB",
    "Redis", "React", "Angular", "Vue", "Node.js", "Django", "Flask",
    "FastAPI", "Spring Boot", ".NET", "Docker", "Kubernetes", "AWS", "Azure",
    "GCP", "Linux", "Git", "CI/CD", "Jenkins", "Terraform", "REST API",
    "GraphQL", "Microservices", "Machine Learning", "Deep Learning", "NLP",
    "TensorFlow", "PyTorch", "Pandas", "NumPy", "Spark", "Hadoop", "Kafka",
    "Power BI", "Tableau", "Excel", "ETL", "Selenium", "Android", "iOS",
    "HTML", "CSS", "Figma", "Cyber Security", "Salesforce", "SAP",
]
_SKILL_PATTERNS = [
    (name, re.compile(r"(?<![A-Za-z0-9+#.])" + re.escape(name) + r"(?![A-Za-z0-9+#])", re.I))
    for name in SKILLS
]


class JobSearchUnavailable(Exception):
    """No job provider is configured or every provider failed."""


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------

def _clean(text: Any) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", str(text or ""))).strip()


def _extract_skills(title: str, description: str) -> List[str]:
    haystack = f"{title} {description}"
    found = [name for name, rx in _SKILL_PATTERNS if rx.search(haystack)]
    return found[:5]


def _job_key(job: Dict[str, Any]) -> str:
    raw = "|".join(
        re.sub(r"[^a-z0-9]", "", str(job.get(k, "")).lower())
        for k in ("title", "company", "location")
    )
    return hashlib.md5(raw.encode()).hexdigest()


def _parse_date(value: Any) -> Optional[float]:
    """ISO-ish date string -> epoch seconds (None if unknown)."""
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    from datetime import datetime, timezone

    for candidate in (text, text[:19], text[:10]):
        try:
            dt = datetime.fromisoformat(candidate)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            continue
    return None


# ----------------------------------------------------------------------
# providers
# ----------------------------------------------------------------------

class AdzunaProvider:
    name = "Adzuna"
    BASE = os.getenv("ADZUNA_BASE_URL", "https://api.adzuna.com/v1/api/jobs")

    @property
    def enabled(self) -> bool:
        return bool(ADZUNA_APP_ID and ADZUNA_APP_KEY)

    @staticmethod
    def countries() -> List[str]:
        """Main country first, then the others from ADZUNA_COUNTRIES."""
        main = (ADZUNA_COUNTRY or "in").strip().lower()
        extra = [
            c.strip().lower()
            for c in str(ADZUNA_COUNTRIES or "").split(",")
            if c.strip()
        ]
        ordered = [main] + [c for c in extra if c != main]
        return ordered[:MAX_COUNTRIES]

    def search(self, q, location, remote, posted_within, sort, page, limit):
        countries = self.countries()
        main = countries[0]

        def one(country):
            try:
                return self._search_country(
                    country, q, location, remote, posted_within, sort, page, limit,
                    # Another country's search for "Kolkata" can return loose
                    # matches; keep only jobs that really mention the place.
                    require_location=bool(location) and country != main
                    and location.lower() != "remote",
                ), None
            except Exception as error:
                logger.warning("Adzuna (%s) search failed: %s", country, error)
                return ([], 0), error

        with ThreadPoolExecutor(max_workers=len(countries)) as pool:
            outcomes = list(pool.map(one, countries))

        if all(error is not None for _r, error in outcomes):
            raise outcomes[0][1]

        jobs: List[Dict[str, Any]] = []
        total = 0
        for (country_jobs, count), error in outcomes:
            if error is None:
                jobs.extend(country_jobs)
                total += count
        return jobs, total

    def _search_country(
        self, country, q, location, remote, posted_within, sort, page, limit,
        require_location=False,
    ):
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "results_per_page": limit,
            "content-type": "application/json",
            "sort_by": "date" if sort == "date" else "relevance",
        }
        what = (q or "").strip()
        if remote:
            what = f"{what} remote".strip()
        if what:
            params["what"] = what
        if location and location.lower() != "remote":
            params["where"] = location
        if posted_within:
            params["max_days_old"] = posted_within

        url = f"{self.BASE}/{country or 'in'}/search/{page}"
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        wanted = (location or "").strip().lower()
        jobs = []
        for item in data.get("results", []) or []:
            where = _clean((item.get("location") or {}).get("display_name"))
            if require_location and wanted not in where.lower():
                continue
            predicted = str(item.get("salary_is_predicted", "0")) == "1"
            jobs.append({
                "id": f"adzuna-{country}-{item.get('id')}",
                "title": _clean(item.get("title")),
                "company": _clean((item.get("company") or {}).get("display_name")),
                "location": where,
                "description": _clean(item.get("description")),
                "url": item.get("redirect_url") or "",
                "posted_at": item.get("created") or "",
                # Adzuna guesses salaries for many jobs; don't show guesses.
                "salary_min": None if predicted else item.get("salary_min"),
                "salary_max": None if predicted else item.get("salary_max"),
                "source": self.name,
            })

        count = int(data.get("count") or len(jobs))
        if require_location:
            count = len(jobs)
        return jobs, count


class JoobleProvider:
    name = "Jooble"
    BASE = "https://jooble.org/api"

    @property
    def enabled(self) -> bool:
        return bool(JOOBLE_API_KEY)

    def search(self, q, location, remote, posted_within, sort, page, limit):
        keywords = (q or "").strip()
        if remote:
            keywords = f"{keywords} remote".strip()

        body: Dict[str, Any] = {
            "keywords": keywords,
            "page": str(page),
            "ResultOnPage": str(limit),
        }
        if location and location.lower() != "remote":
            body["location"] = location
        if posted_within:
            from datetime import date, timedelta

            body["datecreatedfrom"] = (
                date.today() - timedelta(days=int(posted_within))
            ).isoformat()

        response = requests.post(
            f"{self.BASE}/{JOOBLE_API_KEY}",
            json=body,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        jobs = []
        for item in data.get("jobs", []) or []:
            jobs.append({
                "id": f"jooble-{item.get('id') or hashlib.md5(str(item.get('link')).encode()).hexdigest()[:12]}",
                "title": _clean(item.get("title")),
                "company": _clean(item.get("company")),
                "location": _clean(item.get("location")),
                "description": _clean(item.get("snippet")),
                "url": item.get("link") or "",
                "posted_at": item.get("updated") or "",
                "salary": _clean(item.get("salary")),
                "source": self.name,
            })
        return jobs, int(data.get("totalCount") or len(jobs))


# ----------------------------------------------------------------------
# service
# ----------------------------------------------------------------------

def level_matches(selected: str, title: str, description: str) -> Tuple[bool, str]:
    """
    Does a job fit the selected experience level?
    Returns (keep, job_level_name). Jobs that never state a level are kept.
    """
    lvl = job_level(title, description)
    name = LEVEL_NAMES.get(lvl, "") if lvl is not None else ""

    if not selected or lvl is None:
        return True, name

    if selected == "senior":
        return lvl >= 3, name

    return name == selected, name


class JobBoardService:

    def __init__(self):
        self.providers = [AdzunaProvider(), JoobleProvider()]
        self._cache: Dict[Tuple, Tuple[float, Dict[str, Any]]] = {}
        self._lock = threading.Lock()

    @property
    def configured(self) -> bool:
        return any(p.enabled for p in self.providers)

    # -- cache ---------------------------------------------------------

    def _get(self, key):
        with self._lock:
            hit = self._cache.get(key)
            if hit and time.time() - hit[0] < CACHE_TTL:
                return hit[1]
        return None

    def _put(self, key, value):
        with self._lock:
            if len(self._cache) >= CACHE_MAX:
                oldest = min(self._cache, key=lambda k: self._cache[k][0])
                self._cache.pop(oldest, None)
            self._cache[key] = (time.time(), value)

    # -- search --------------------------------------------------------

    def search(
        self,
        q: str = "",
        location: str = "",
        level: str = "",
        remote: bool = False,
        posted_within: int = 0,
        sort: str = "relevance",
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:

        active = [p for p in self.providers if p.enabled]

        if not active:
            raise JobSearchUnavailable("No job provider is configured.")

        key = (q.lower(), location.lower(), level, remote, posted_within, sort, page, limit)
        cached = self._get(key)
        if cached is not None:
            return cached

        def run(provider):
            try:
                return provider.name, provider.search(
                    q, location, remote, posted_within, sort, page, limit
                ), None
            except Exception as error:      # network, bad JSON, quota...
                logger.warning("%s job search failed: %s", provider.name, error)
                return provider.name, ([], 0), error

        with ThreadPoolExecutor(max_workers=len(active)) as pool:
            outcomes = list(pool.map(run, active))

        if all(error is not None for _n, _r, error in outcomes):
            raise JobSearchUnavailable("All job providers failed.")

        merged: List[Dict[str, Any]] = []
        total = 0
        has_more = False

        for _name, (jobs, count), error in outcomes:
            if error is not None:
                continue
            total += count
            if page * limit < count:
                has_more = True
            merged.extend(jobs)

        # -- dedupe (first provider wins) --------------------------
        seen, unique = set(), []
        for job in merged:
            if not job["title"] or not job["url"]:
                continue
            k = _job_key(job)
            if k in seen:
                continue
            seen.add(k)
            unique.append(job)

        # -- level / remote filters + enrichment -------------------
        results = []
        for job in unique:
            text = f"{job['title']} {job['description']}"

            keep, level_name = level_matches(level, job["title"], job["description"])
            if not keep:
                continue

            is_remote = bool(REMOTE_RE.search(f"{job['title']} {job['location']} {job['description'][:400]}"))
            if remote and not is_remote:
                continue

            job["level"] = level_name
            job["remote"] = is_remote
            job["skills"] = _extract_skills(job["title"], job["description"])
            job["description"] = job["description"][:400]
            results.append(job)

        # -- ranking -----------------------------------------------
        if sort == "date":
            results.sort(key=lambda j: _parse_date(j.get("posted_at")) or 0, reverse=True)
        else:
            words = [w for w in re.split(r"\W+", q.lower()) if len(w) > 1]

            def score(job):
                title = job["title"].lower()
                hits = sum(1 for w in words if w in title)
                stated = 1 if (level and job["level"] == level) else 0
                return (hits, stated)

            results.sort(key=score, reverse=True)      # stable: provider order kept on ties

        response = {
            "jobs": results,
            "total": total,
            "page": page,
            "has_more": has_more,
        }

        self._put(key, response)
        return response


_service: Optional[JobBoardService] = None


def get_job_board() -> JobBoardService:
    global _service
    if _service is None:
        _service = JobBoardService()
    return _service
