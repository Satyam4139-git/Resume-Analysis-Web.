import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# PROJECT ROOT
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

# Explicitly load the project's .env file.
ENV_FILE = BASE_DIR / ".env"

# override=True ensures that values from the project's .env
# override stale Windows environment variables.
load_dotenv(
    ENV_FILE,
    override=True,
)


# ============================================================
# OPENROUTER / AI CONFIGURATION
# ============================================================

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "nvidia/nemotron-3-super-120b-a12b:free",
)

MAX_OUTPUT_TOKENS = int(
    os.getenv(
        "MAX_OUTPUT_TOKENS",
        "1200",
    )
)

RESUME_PARSER_MAX_TOKENS = int(
    os.getenv(
        "RESUME_PARSER_MAX_TOKENS",
        "4000",
    )
)

AI_REVIEW_MAX_TOKENS = int(
    os.getenv(
        "AI_REVIEW_MAX_TOKENS",
        "2000",
    )
)

# Hard limit (seconds) on how long AI may take to refine the parsed resume.
# After this the instant local parse is used. Lower = faster, higher = more AI help.
AI_PARSE_BUDGET_SECONDS = float(
    os.getenv(
        "AI_PARSE_BUDGET_SECONDS",
        "8",
    )
)

# Budget (seconds) for the AI review + improvement tips.
AI_REVIEW_BUDGET_SECONDS = float(
    os.getenv(
        "AI_REVIEW_BUDGET_SECONDS",
        "30",
    )
)

TEMPERATURE = float(
    os.getenv(
        "TEMPERATURE",
        "0.2",
    )
)

BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1",
)


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

DEVELOPMENT_MODE = (
    os.getenv(
        "DEVELOPMENT_MODE",
        "false",
    ).lower()
    == "true"
)


# ============================================================
# GOOGLE AUTHENTICATION
# ============================================================

GOOGLE_CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID"
)

GOOGLE_CLIENT_SECRET = os.getenv(
    "GOOGLE_CLIENT_SECRET"
)

# On Render, RENDER_EXTERNAL_URL is set automatically
# (e.g. https://your-name.onrender.com), so these work with no setup.
PUBLIC_URL = (
    os.getenv("PUBLIC_URL")
    or os.getenv("RENDER_EXTERNAL_URL")
    or ""
).rstrip("/")

GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    (
        f"{PUBLIC_URL}/auth/callback"
        if PUBLIC_URL
        else "http://127.0.0.1:8000/auth/callback"
    ),
)


# ============================================================
# SESSION
# ============================================================

SESSION_SECRET = os.getenv("SESSION_SECRET")

if not SESSION_SECRET:

    # Never crash the whole site over this. A random secret works, but
    # logins are reset on every restart - set SESSION_SECRET in production.
    import secrets

    SESSION_SECRET = secrets.token_urlsafe(48)

    print(
        "WARNING: SESSION_SECRET is not set. Using a temporary random "
        "secret; users will be logged out on every restart."
    )

# Secure (https-only) cookies in production; plain http works locally.
SESSION_HTTPS_ONLY = (
    os.getenv(
        "SESSION_HTTPS_ONLY",
        "true" if PUBLIC_URL.startswith("https://") else "false",
    ).lower()
    == "true"
)


# ============================================================
# FRONTEND
# ============================================================

# The site is served by this same backend, so the frontend URL is the
# public URL. Only set FRONTEND_URL if the frontend is hosted elsewhere.
FRONTEND_URL = (
    os.getenv("FRONTEND_URL")
    or PUBLIC_URL
    or "http://127.0.0.1:8000"
).rstrip("/")


# ============================================================
# ADZUNA
# ============================================================

ADZUNA_APP_ID = os.getenv(
    "ADZUNA_APP_ID"
)

ADZUNA_APP_KEY = os.getenv(
    "ADZUNA_APP_KEY"
)

# Main Adzuna country.
#
# For the current project we are using India.
ADZUNA_COUNTRY = os.getenv(
    "ADZUNA_COUNTRY",
    "in",
)

# Countries available for future expansion.
ADZUNA_COUNTRIES = os.getenv(
    "ADZUNA_COUNTRIES",
    "in,gb,us,au,ca",
)

# Jooble (optional second job source). Leave empty to use Adzuna only.
JOOBLE_API_KEY = os.getenv(
    "JOOBLE_API_KEY"
)

ADZUNA_RESULTS_PER_PAGE = int(
    os.getenv(
        "ADZUNA_RESULTS_PER_PAGE",
        "10",
    )
)

MAX_JOB_RESULTS = int(
    os.getenv(
        "MAX_JOB_RESULTS",
        "20",
    )
)


# ============================================================
# INDIA-FIRST JOB RECOMMENDATIONS
# ============================================================

# When True, the job-search system prioritizes Indian jobs.
INDIA_FIRST_JOBS = (
    os.getenv(
        "INDIA_FIRST_JOBS",
        "true",
    ).lower()
    == "true"
)

# Additional ranking points for an Indian company.
INDIAN_COMPANY_BOOST = int(
    os.getenv(
        "INDIAN_COMPANY_BOOST",
        "20",
    )
)

# Additional ranking points for an Indian job location.
INDIAN_LOCATION_BOOST = int(
    os.getenv(
        "INDIAN_LOCATION_BOOST",
        "10",
    )
)


# ============================================================
# VALIDATION
# ============================================================

if not OPENROUTER_API_KEY:

    raise RuntimeError(
        "OPENROUTER_API_KEY is missing. "
        "Please configure it in the .env file."
    )


# ============================================================
# DEBUG INFORMATION
# ============================================================

print("=" * 70)
print("Resume Analyzer Configuration")
print("=" * 70)

print(
    "ENV FILE:",
    ENV_FILE,
)

print(
    "ENV EXISTS:",
    ENV_FILE.exists(),
)

print(
    "MODEL_NAME:",
    MODEL_NAME,
)

print(
    "MAX_OUTPUT_TOKENS:",
    MAX_OUTPUT_TOKENS,
)

print(
    "RESUME_PARSER_MAX_TOKENS:",
    RESUME_PARSER_MAX_TOKENS,
)

print(
    "AI_REVIEW_MAX_TOKENS:",
    AI_REVIEW_MAX_TOKENS,
)

print(
    "TEMPERATURE:",
    TEMPERATURE,
)

print(
    "DEVELOPMENT_MODE:",
    DEVELOPMENT_MODE,
)

print(
    "ADZUNA_COUNTRY:",
    ADZUNA_COUNTRY,
)

print(
    "ADZUNA_COUNTRIES:",
    ADZUNA_COUNTRIES,
)

print(
    "ADZUNA_RESULTS_PER_PAGE:",
    ADZUNA_RESULTS_PER_PAGE,
)

print(
    "MAX_JOB_RESULTS:",
    MAX_JOB_RESULTS,
)

print(
    "INDIA_FIRST_JOBS:",
    INDIA_FIRST_JOBS,
)

print(
    "INDIAN_COMPANY_BOOST:",
    INDIAN_COMPANY_BOOST,
)

print(
    "INDIAN_LOCATION_BOOST:",
    INDIAN_LOCATION_BOOST,
)

print("=" * 70)