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

REMOTIVE_API = "https://remotive.com/api/remote-jobs"

# =========================
# STICKY KEY ROTATION MEMORY
# =========================
current_key_index = 0

# =========================
# COUNTRY MAP
# =========================
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
    "Italy": "it",
    "Singapore": "sg",
    "Brazil": "br",
    "South Africa": "za",
    "Mexico": "mx",
    "Poland": "pl",
    "Belgium": "be",
    "Austria": "at",
    "Switzerland": "ch"
}

from backend.utils.helpers import (
    normalize_date,
    parse_date,
    skill_match,
    work_mode,
    excel_link
)

# =========================================================
# SAFE REQUEST HELPER WITH STICKY FAILOVER
# =========================================================
def safe_json_request(method, url, **kwargs):
    global current_key_index

    try:
        # RAPIDAPI ROTATION
        if "rapidapi" in url and RAPIDAPI_KEYS and RAPIDAPI_KEYS != [""]:

            total = len(RAPIDAPI_KEYS)

            for i in range(total):

                idx = (current_key_index + i) % total
                key = RAPIDAPI_KEYS[idx]

                headers = kwargs.get("headers", {})
                headers["x-rapidapi-key"] = key
                headers["x-rapidapi-host"] = "jsearch.p.rapidapi.com"
                kwargs["headers"] = headers

                print(f"\n🔑 Trying RapidAPI Key: {key[:6]}****")

                r = requests.request(method, url, timeout=20, **kwargs)

                print(f"➡️ Status Code: {r.status_code}")

                # SUCCESS
                if r.status_code == 200:
                    data = r.json()
                    count = len(data.get("data", []))

                    print(f"✅ RapidAPI Jobs Received: {count}")

                    # SAVE WORKING KEY
                    current_key_index = idx

                    return data

                # RATE LIMIT → try next key
                if r.status_code in (403, 429):
                    print("⚠️ Key exhausted → trying next")
                    continue

                print("❌ API ERROR:", r.text[:200])

            print("🚨 ALL RAPIDAPI KEYS EXHAUSTED")
            return {}

        # NON RAPIDAPI CALL
        r = requests.request(method, url, timeout=20, **kwargs)

        if r.status_code != 200:
            print("❌ API ERROR:", url, r.status_code)
            return {}

        return r.json()

    except Exception as e:
        print("❌ REQUEST FAILED:", url, e)
        return {}

# =========================================================
# REMOTE JOBS
# =========================================================
def fetch_remote_jobs(skills, level, posted_days):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for skill in skills:
        data = safe_json_request(
            "GET",
            "https://jsearch.p.rapidapi.com/search",
            params={"query": f"{skill} {level} remote job", "num_pages": 1}
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

    remotive = safe_json_request("GET", REMOTIVE_API)

    for skill in skills:
        for j in remotive.get("jobs", []):
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

    for f in feeds:
        feed = feedparser.parse(f)

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
                        "Apply": e.link,
                        "_excel": excel_link(e.link),
                        "_date": None
                    })
    return rows

def fetch_arbeitnow(skills):
    rows = []
    data = safe_json_request("GET", "https://www.arbeitnow.com/api/job-board-api")

    for j in data.get("data", []):
        for skill in skills:
            if not skill_match(j.get("title",""), skill):
                continue

            rows.append({
                "Source": "Arbeitnow",
                "Skill": skill,
                "Title": j.get("title"),
                "Company": j.get("company_name"),
                "Location": j.get("location"),
                "Work Mode": "Remote" if j.get("remote") else "On-site",
                "Apply": j.get("url"),
                "_excel": excel_link(j.get("url")),
                "_date": None
            })
    return rows

# =========================================================
# MAIN FETCHERS
# =========================================================
def fetch_jsearch(skills, levels, countries, posted_days, location):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for skill in skills:
        data = safe_json_request(
            "GET",
            "https://jsearch.p.rapidapi.com/search",
            params={"query": f"{skill} job {location}".strip(), "num_pages": 1}
        )

        print(f"JSearch returned {len(data.get('data', []))} jobs")

        for j in data.get("data", []):
            dt = normalize_date(j.get("job_posted_at_datetime_utc"))

            if dt and dt < cutoff:
                continue

            rows.append({
                "Source": "JSearch",
                "Skill": skill,
                "Title": j.get("job_title"),
                "Company": j.get("employer_name"),
                "Location": j.get("job_city"),
                "Country": j.get("job_country"),
                "Work Mode": j.get("job_employment_type"),
                "Apply": j.get("job_apply_link"),
                "_excel": excel_link(j.get("job_apply_link")),
                "_date": dt
            })

    return rows
