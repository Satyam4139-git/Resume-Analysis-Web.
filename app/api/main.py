from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes.applications import router as applications_router

from app.api.routes import (
    health,
    resume,
    analysis,
    auth,
    jobs,
)

from app.core.branding import DOCS_CSS, error_page
from app.core.config import (
    SESSION_SECRET,
    SESSION_HTTPS_ONLY,
    FRONTEND_URL,
    PUBLIC_URL,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_INDEX = FRONTEND_DIR / "index.html"


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="CareerPilot AI API",
    description="Resume analysis, ATS scoring, job search and application tracking",
    version="1.0.0",
    docs_url=None,      # replaced by the branded /docs page below
    redoc_url=None,
)


# ============================================================
# SESSION MIDDLEWARE
# ============================================================

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="ai_career_session",
    max_age=60 * 60 * 24 * 7,
    same_site="none",
    https_only=SESSION_HTTPS_ONLY,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(
        {
            origin
            for origin in (
                FRONTEND_URL,
                PUBLIC_URL,
                "http://127.0.0.1:8000",
                "http://localhost:8000",
            )
            if origin
        }
    ),
    allow_credentials=True,
    allow_methods=[
        "*",
    ],
    allow_headers=[
        "*",
    ],
)


# ============================================================
# API ROUTES
# ============================================================

app.include_router(
    health.router
)

app.include_router(
    resume.router
)

app.include_router(
    analysis.router
)

app.include_router(
    auth.router
)

app.include_router(
    applications_router
)

app.include_router(
    jobs.router
)


# ============================================================
# FRONTEND
# ============================================================

@app.get("/", include_in_schema=False)
def serve_frontend():
    """
    Serve the main frontend application.
    """

    if not FRONTEND_INDEX.exists():
        return {
            "success": False,
            "message": "Frontend index.html not found.",
        }

    return FileResponse(
        FRONTEND_INDEX,
        media_type="text/html; charset=utf-8",
    )


@app.get("/style.css", include_in_schema=False)
def serve_stylesheet():
    """
    Serve the frontend stylesheet.
    """

    stylesheet = FRONTEND_DIR / "style.css"

    if not stylesheet.exists():
        return {
            "success": False,
            "message": "Frontend style.css not found.",
        }

    return FileResponse(
        stylesheet,
        media_type="text/css; charset=utf-8",
    )


@app.get("/jobs.js", include_in_schema=False)
def serve_jobs_javascript():
    """
    Serve the job search page JavaScript.
    """

    javascript = FRONTEND_DIR / "jobs.js"

    if not javascript.exists():
        return {
            "success": False,
            "message": "Frontend jobs.js not found.",
        }

    return FileResponse(
        javascript,
        media_type="application/javascript; charset=utf-8",
    )


@app.get("/app.js", include_in_schema=False)
def serve_javascript():
    """
    Serve the frontend JavaScript.
    """

    javascript = FRONTEND_DIR / "app.js"

    if not javascript.exists():
        return {
            "success": False,
            "message": "Frontend app.js not found.",
        }

    return FileResponse(
        javascript,
        media_type="application/javascript; charset=utf-8",
    )


# ============================================================
# DEPLOYMENT HEALTH CHECK (no trailing slash, for the host)
# ============================================================

@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}


# ============================================================
# BRANDED BACKEND PAGES (same palette as the website)
# ============================================================

@app.get("/theme.css", include_in_schema=False)
def serve_theme():
    return FileResponse(
        FRONTEND_DIR / "theme.css",
        media_type="text/css; charset=utf-8",
    )


@app.get("/docs", include_in_schema=False)
def branded_docs():
    page = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="CareerPilot AI API",
    )
    body = page.body.decode("utf-8").replace("</head>", DOCS_CSS + "</head>", 1)
    return HTMLResponse(body)


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    """Branded HTML page for browsers; plain JSON for API/fetch calls."""

    accepts = request.headers.get("accept", "")

    if "text/html" in accepts and not request.url.path.startswith(
        ("/resume", "/analysis", "/applications", "/jobs")
    ):
        return HTMLResponse(
            error_page(exc.status_code, str(exc.detail or "")),
            status_code=exc.status_code,
        )

    from fastapi.responses import JSONResponse

    return JSONResponse(
        {"detail": exc.detail},
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None),
    )


# ============================================================
# ALWAYS SHOW THE LATEST FRONTEND (no stale CSS/JS after updates)
# ============================================================

@app.middleware("http")
async def revalidate_static_files(request: Request, call_next):
    response = await call_next(request)
    if request.url.path in {"/", "/app.js", "/jobs.js", "/style.css", "/theme.css"}:
        response.headers["Cache-Control"] = "no-cache"
    return response
