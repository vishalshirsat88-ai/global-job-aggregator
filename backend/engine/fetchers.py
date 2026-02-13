import os
import requests
import feedparser
from datetime import datetime, timedelta

# =========================
# ENV VARIABLES
# =========================
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
JOOBLE_KEY = os.getenv("JOOBLE_KEY")
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")
USAJOBS_EMAIL = os.getenv("USAJOBS_EMAIL")
USAJOBS_API_KEY = os.getenv("USAJOBS_API_KEY")

REMOTIVE_API = "https://remotive.com/api/remote-jobs"

COUNTRIES = {
    "India": "in",
    "United States": "us",
    "United Kingdom": "gb",
    "United Arab Emirates": "ae",
    "Canada": "ca",
    "Australia": "au",
    "Germany": "de",
    "France": "fr",
    "Netherlands": "nl",
    "Ireland": "ie",
    "Spain": "es",
    "Italy": "it"
}

from backend.utils.helpers import (
    normalize_date,
    parse_date,
    skill_match,
    work_mode,
    excel_link
)

# =========================================================
# 🛡️ SAFE REQUEST HELPER
# =========================================================
def safe_json_request(method, url, **kwargs):
    """
    Universal safe API caller:
    - Handles non-200 responses
    - Handles empty responses
    - Handles invalid JSON
    - Never crashes backend
    """
    try:
        r = requests.request(method, url, timeout=20, **kwargs)

        if r.status_code != 200:
            print(f"⚠️ API ERROR {url} → {r.status_code}")
            return {}

        if not r.text:
            print(f"⚠️ EMPTY RESPONSE → {url}")
            return {}

        return r.json()

    except Exception as e:
        print(f"⚠️ REQUEST FAILED {url} → {e}")
        return {}


# =========================================================
# REMOTE SEARCH
# =========================================================
def fetch_remote_jobs(skills, level, posted_days):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for skill in skills:
        data = safe_json_request(
            "GET",
            "https://jsearch.p.rapidapi.com/search",
            headers={
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": "jsearch.p.rapidapi.com"
            },
            params={
                "query": f"{skill} {level} remote job",
                "num_pages": 1
            }
        )

        for j in data.get("data", []):
            blob = f"{j.get('job_title','')} {j.get('job_description','')}"
            if not skill_match(blob, skill):
                continue

            dt = parse_date(j.get("job_posted_at_datetime_utc",""))
            if dt and dt < cutoff:
                continue

            rows.append({
                "Source": j.get("job_publisher",""),
                "Skill": skill,
                "Title": j.get("job_title"),
                "Company": j.get("employer_name"),
                "Location": "Remote",
                "Country": "Remote",
                "Work Mode": "Remote",
                "Posted": j.get("job_posted_at_datetime_utc",""),
                "Apply": j.get("job_apply_link"),
                "_excel": excel_link(j.get("job_apply_link")),
                "_date": dt
            })

    remotive_data = safe_json_request("GET", REMOTIVE_API)

    for skill in skills:
        for j in remotive_data.get("jobs", []):
            if not skill_match(j.get("title",""), skill):
                continue

            rows.append({
                "Source": "Remotive",
                "Skill": skill,
                "Title": j.get("title"),
                "Company": j.get("company_name"),
                "Location": "Remote",
                "Country": "Remote",
                "Work Mode": "Remote",
                "Posted": "",
                "Apply": j.get("url"),
                "_excel": excel_link(j.get("url")),
                "_date": None
            })

    return rows


# =========================================================
# RSS FETCHERS
# =========================================================
def fetch_weworkremotely(skills):
    rows = []
    feeds = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-management-jobs.rss"
    ]

    for feed_url in feeds:
        feed = feedparser.parse(feed_url)

        for e in feed.entries:
            for skill in skills:
                if e.title and skill.lower() in e.title.lower():
                    rows.append({
                        "Source": "WeWorkRemotely",
                        "Skill": skill,
                        "Title": e.title,
                        "Company": "",
                        "Location": "Remote",
                        "Country": "Remote",
                        "Work Mode": "Remote",
                        "Posted": "",
                        "Apply": e.link,
                        "_excel": excel_link(e.link),
                        "_date": None
                    })

    return rows


def fetch_arbeitnow(skills):
    rows = []

    data = safe_json_request(
        "GET",
        "https://www.arbeitnow.com/api/job-board-api"
    )

    for j in data.get("data", []):
        for skill in skills:
            if not skill_match(j.get("title", ""), skill):
                continue

            rows.append({
                "Source": "Arbeitnow",
                "Skill": skill,
                "Title": j.get("title"),
                "Company": j.get("company_name"),
                "Location": j.get("location"),
                "Country": None,
                "Work Mode": "Remote" if j.get("remote") else "On-site",
                "Posted": "",
                "Apply": j.get("url"),
                "_excel": excel_link(j.get("url")),
                "_date": None
            })

    return rows


# =========================================================
# NON-REMOTE FETCHERS
# =========================================================
def fetch_jsearch(skills, levels, countries, posted_days, location):
    rows = []

    for skill in skills:
        data = safe_json_request(
            "GET",
            "https://jsearch.p.rapidapi.com/search",
            headers={
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": "jsearch.p.rapidapi.com"
            },
            params={
                "query": f"{skill} job {location}".strip(),
                "page": 1,
                "num_pages": 1
            }
        )

        for j in data.get("data", []):
            rows.append({
                "Source": "JSearch",
                "Skill": skill,
                "Title": j.get("job_title"),
                "Company": j.get("employer_name"),
                "Location": j.get("job_city"),
                "Country": j.get("job_country"),
                "Work Mode": j.get("job_employment_type"),
                "Posted": j.get("job_posted_at_datetime_utc"),
                "Apply": j.get("job_apply_link"),
                "_date": normalize_date(j.get("job_posted_at_datetime_utc"))
            })

    return rows


def fetch_adzuna(skills, levels, countries, posted_days, location):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for c in countries:
        if c not in COUNTRIES:
            continue

        data = safe_json_request(
            "GET",
            f"https://api.adzuna.com/v1/api/jobs/{COUNTRIES[c]}/search/1",
            params={
                "app_id": ADZUNA_APP_ID,
                "app_key": ADZUNA_API_KEY,
                "what": " OR ".join(skills + levels),
                "where": location or "",
                "results_per_page": 20
            }
        )

        for j in data.get("results", []):
            dt = normalize_date(j.get("created",""))
            if dt and dt < cutoff:
                continue

            rows.append({
                "Source": "Adzuna",
                "Skill": ", ".join(skills),
                "Title": j.get("title"),
                "Company": j.get("company",{}).get("display_name"),
                "Location": j.get("location",{}).get("display_name"),
                "Country": c,
                "Work Mode": work_mode(j.get("title","")),
                "Posted": j.get("created",""),
                "Apply": j.get("redirect_url"),
                "_excel": excel_link(j.get("redirect_url")),
                "_date": dt
            })

    return rows


def fetch_jooble(skills, levels, countries, location):
    rows = []

    for c in countries:
        data = safe_json_request(
            "POST",
            f"https://jooble.org/api/{JOOBLE_KEY}",
            json={
                "keywords": " ".join(skills + levels),
                "location": location or c
            }
        )

        for j in data.get("jobs", []):
            rows.append({
                "Source": "Jooble",
                "Skill": ", ".join(skills),
                "Title": j.get("title"),
                "Company": j.get("company"),
                "Location": j.get("location"),
                "Country": None,
                "Work Mode": work_mode(j.get("title","")),
                "Posted": "",
                "Apply": j.get("link"),
                "_excel": excel_link(j.get("link")),
                "_date": None
            })

    return rows


def fetch_usajobs(skills, posted_days):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for skill in skills:
        data = safe_json_request(
            "GET",
            "https://data.usajobs.gov/api/search",
            headers={
                "User-Agent": USAJOBS_EMAIL,
                "Authorization-Key": USAJOBS_API_KEY
            },
            params={
                "Keyword": skill,
                "ResultsPerPage": 25
            }
        )

        items = data.get("SearchResult", {}).get("SearchResultItems", [])

        for j in items:
            d = j["MatchedObjectDescriptor"]

            rows.append({
                "Source": "USAJobs",
                "Skill": skill,
                "Title": d["PositionTitle"],
                "Company": d["OrganizationName"],
                "Location": ", ".join(
                    l["LocationName"] for l in d.get("PositionLocation", [])
                ),
                "Country": "UNITED STATES",
                "Work Mode": "On-site",
                "Posted": d.get("PublicationStartDate", ""),
                "Apply": d["PositionURI"],
                "_excel": excel_link(d["PositionURI"]),
                "_date": normalize_date(d.get("PublicationStartDate", ""))
            })

    return rows
