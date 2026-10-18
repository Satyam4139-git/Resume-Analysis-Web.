import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import APIRouter, HTTPException, Query, Request

from app.core.logger import logger
from app.jobs.job_board import (
    VALID_LEVELS,
    JobSearchUnavailable,
    get_job_board,
)

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# Public endpoint backed by a quota-limited API: cap each visitor.
RATE_LIMIT = 30          # requests ...
RATE_WINDOW = 60         # ... per this many seconds
_hits: Dict[str, Deque[float]] = defaultdict(deque)


def _check_rate(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    bucket = _hits[ip]

    while bucket and now - bucket[0] > RATE_WINDOW:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Too many searches. Please wait a minute and try again.",
        )

    bucket.append(now)

    if len(_hits) > 5000:                       # keep memory bounded
        for key in [k for k, v in _hits.items() if not v]:
            _hits.pop(key, None)


@router.get("/status")
def job_sources_status():
    """Which job sources are switched on and how their last search went
    (no keys are ever shown)."""
    return {"providers": get_job_board().status()}


@router.get("/search")
def search_jobs(
    request: Request,
    q: str = Query("", max_length=80),
    location: str = Query("", max_length=60),
    level: str = Query("", max_length=10),
    remote: bool = False,
    posted_within: int = Query(0, ge=0, le=60),
    sort: str = Query("relevance", pattern="^(relevance|date)$"),
    page: int = Query(1, ge=1, le=50),
    limit: int = Query(20, ge=1, le=30),
):
    """
    Search real job postings from Adzuna (and Jooble when configured).
    """

    _check_rate(request)

    q = q.strip()
    location = location.strip()
    level = level.strip().lower()

    if not q and not location:
        raise HTTPException(
            status_code=400,
            detail="Type a job title, skill or city to search.",
        )

    if level and level not in VALID_LEVELS:
        raise HTTPException(
            status_code=400,
            detail="Experience level must be fresher, junior, mid or senior.",
        )

    try:
        return get_job_board().search(
            q=q,
            location=location,
            level=level,
            remote=remote,
            posted_within=posted_within,
            sort=sort,
            page=page,
            limit=limit,
        )

    except JobSearchUnavailable as error:
        logger.error("Job search unavailable: %s", error)
        raise HTTPException(
            status_code=503,
            detail="Job search is temporarily unavailable.",
        )
