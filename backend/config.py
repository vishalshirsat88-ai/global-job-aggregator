import os

# =========================================================
# REQUIRED ENV VARS (names only)
# =========================================================
REQUIRED_ENV_VARS = [
    "RAPIDAPI_KEY",
    "JOOBLE_KEY",
    "ADZUNA_APP_ID",
    "ADZUNA_API_KEY",
    "USAJOBS_API_KEY",
    "USAJOBS_EMAIL",
]

# =========================================================
# SAFETY CHECK (fail fast)
# =========================================================
def validate_env():
    missing = []

    for key in REQUIRED_ENV_VARS:
        if not os.getenv(key):
            missing.append(key)

    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )






# =========================================================
# CONSTANT ENDPOINTS
# =========================================================

REMOTIVE_API = "https://remotive.com/api/remote-jobs"
