import os
import requests
import feedparser
from datetime import datetime, timedelta

# =========================
# ENV VARIABLES
# =========================
RAPIDAPI_KEYS = os.getenv("RAPIDAPI_KEYS", "").split(",")
JOOBLE_KEY = os.getenv("JOOBLE_KEY")
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")
USAJOBS_EMAIL = os.getenv("USAJOBS_EMAIL")
USAJOBS_API_KEY = os.getenv("USAJOBS_API_KEY")

CURRENT_KEY_INDEX = 0
REMOTIVE_API = "https://remotive.com/api/remote-jobs"

from backend.utils.helpers import (
    normalize_date,
    parse_date,
    skill_match,
    work_mode,
    excel_link
)

# =========================================================
# 🔑 RAPIDAPI KEY ROTATION
# =========================================================
def get_rapidapi_key():
    global CURRENT_KEY_INDEX
    if not RAPIDAPI_KEYS:
        return None
    return RAPIDAPI_KEYS[CURRENT_KEY_INDEX % len(RAPIDAPI_KEYS)].strip()

def rotate_key():
    global CURRENT_KEY_INDEX
    CURRENT_KEY_INDEX += 1


# =========================================================
# 🧠 SMART QUERY EXPANSION
# =========================================================
def expand_skill(skill):
    skill = skill.lower()

    expansions = {
        "python": ["python developer", "django developer", "fastapi engineer"],
        "java": ["java developer", "spring boot developer"],
        "react": ["react developer", "frontend react"],
        "data": ["data analyst", "data scientist", "data engineer"]
    }

    return expansions.get(skill, [skill])


# =========================================================
# 🎯 RELEVANCE SCORING FILTER
# =========================================================
def relevance_score(job_title, location, skill, user_location):
    score = 0

    title = (job_title or "").lower()
    loc = (location or "").lower()
    skill = skill.lower()

    if skill in title:
        score += 50

    if user_location and user_location.lower() in loc:
        score += 20

    if "senior" in title or "lead" in title:
        score += 10

    return score


# =========================================================
# 🛡️ SAFE REQUEST WITH KEY ROTATION
# =========================================================
def safe_json_request(method, url, **kwargs):
    max_attempts = len(RAPIDAPI_KEYS) if RAPIDAPI_KEYS else 1

    for _ in range(max_attempts):
        try:
            headers = kwargs.get("headers", {})

            if "rapidapi" in url:
                headers["x-rapidapi-key"] = get_rapidapi_key()
                headers["x-rapidapi-host"] = "jsearch.p.rapidapi.com"
                kwargs["headers"] = headers

            r = requests.request(method, url, timeout=20, **kwargs)

            if r.status_code == 429:
                rotate_key()
                continue

            if r.status_code != 200:
                return {}

            return r.json()

        except:
            rotate_key()

    return {}


# =========================================================
# REMOTE SEARCH
# =========================================================
def fetch_remote_jobs(skills, level, posted_days):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for skill in skills:
        queries = expand_skill(skill)

        for q in queries:
            data = safe_json_request(
                "GET",
                "https://jsearch.p.rapidapi.com/search",
                params={"query": f"{q} remote", "num_pages": 1}
            )

            for j in data.get("data", []):
                dt = parse_date(j.get("job_posted_at_datetime_utc",""))
                if dt and dt < cutoff:
                    continue

                rows.append({
                    "Source": j.get("job_publisher"),
                    "Skill": skill,
                    "Title": j.get("job_title"),
                    "Company": j.get("employer_name"),
                    "Location": "Remote",
                    "Country": "Remote",
                    "Work Mode": "Remote",
                    "Posted": j.get("job_posted_at_datetime_utc"),
                    "Apply": j.get("job_apply_link"),
                    "_excel": excel_link(j.get("job_apply_link")),
                    "_date": dt
                })

    return rows


# =========================================================
# JOOBLE FETCHER WITH SMART FILTER
# =========================================================
def fetch_jooble(skills, levels, countries, location):
    rows = []

    for skill in skills:
        data = safe_json_request(
            "POST",
            f"https://jooble.org/api/{JOOBLE_KEY}",
            json={
                "keywords": skill,
                "location": location
            }
        )

        for j in data.get("jobs", []):
            score = relevance_score(
                j.get("title"),
                j.get("location"),
                skill,
                location
            )

            if score < 40:
                continue

            rows.append({
                "Source": "Jooble",
                "Skill": skill,
                "Title": j.get("title"),
                "Company": j.get("company"),
                "Location": j.get("location"),
                "Country": None,
                "Work Mode": work_mode(j.get("title")),
                "Posted": "",
                "Apply": j.get("link"),
                "_excel": excel_link(j.get("link")),
                "_date": None
            })

    return rows
