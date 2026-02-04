import requests
import streamlit as st
import feedparser
from datetime import datetime, timedelta

from engine.utils import (
    normalize_date,
    parse_date,
    skill_match,
    work_mode,
    excel_link
)

# =========================================================
# REMOTE SEARCH
# =========================================================
def fetch_remote_jobs(skills, level, posted_days):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for skill in skills:
        r = requests.get(
            "https://jsearch.p.rapidapi.com/search",
            headers={
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": "jsearch.p.rapidapi.com"
            },
            params={
                "query": f"{skill} {level} remote job",
                "num_pages": 1
            },
            timeout=20
        )

        if r.status_code == 200:
            for j in r.json().get("data", []):
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

    r = requests.get(REMOTIVE_API, timeout=15).json()
    for skill in skills:
        for j in r.get("jobs", []):
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
                if not skill_match(e.title, skill):
                    continue

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
    r = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=15)

    if r.status_code != 200:
        return rows

    for j in r.json().get("data", []):
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
        cutoff = datetime.utcnow() - timedelta(days=posted_days)
    
        for skill in skills:
            query = f"{skill} job {location}".strip()
    
            try:
                r = requests.get(
                    "https://jsearch.p.rapidapi.com/search",
                    headers={
                        "x-rapidapi-key": RAPIDAPI_KEY,
                        "x-rapidapi-host": "jsearch.p.rapidapi.com"
                    },
                    params={
                        "query": query,
                        "num_pages": 2
                    },
                    timeout=15   # ⬅ slightly lower is better
                )
            except requests.exceptions.ReadTimeout:
                continue   # skip this call, keep looping
            except requests.exceptions.RequestException:
                continue
    
    
    
            if r.status_code != 200:
                continue
    
            for j in r.json().get("data", []):
                dt = normalize_date(j.get("job_posted_at_datetime_utc",""))
                if dt and dt < cutoff:
                    continue
    
                rows.append({
                    "Source": j.get("job_publisher",""),
                    "Skill": skill,
                    "Title": j.get("job_title"),
                    "Company": j.get("employer_name"),
                    "Location": j.get("job_city") or j.get("job_state") or "",
                    "Country": (j.get("job_country") or "").upper(),
                    "Work Mode": work_mode(j.get("job_description","")),
                    "Posted": j.get("job_posted_at_datetime_utc",""),
                    "Apply": j.get("job_apply_link"),
                    "_excel": excel_link(j.get("job_apply_link")),
                    "_date": dt
                })
    
        return rows
    
    
    
    def fetch_adzuna(skills, levels, countries, posted_days, location):
        rows = []
        cutoff = datetime.utcnow() - timedelta(days=posted_days)
    
        for c in countries:
            r = requests.get(
                f"https://api.adzuna.com/v1/api/jobs/{COUNTRIES[c]}/search/1",
                params={
                    "app_id": ADZUNA_APP_ID,
                    "app_key": ADZUNA_API_KEY,
                    "what": " OR ".join(skills + levels),
                  "where": location or "",   # let Adzuna search country-wide  # ✅ CITY USED
                    "results_per_page": 20
                },
                timeout=15
            ).json()
    
            for j in r.get("results", []):
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
            r = requests.post(
                f"https://jooble.org/api/{JOOBLE_KEY}",
                json={
                    "keywords": " ".join(skills + levels),
                    "location": location or c   # country-level search only
                },
                timeout=15
            ).json()
    
            for j in r.get("jobs", []):
                rows.append({
                    "Source": "Jooble",
                    "Skill": ", ".join(skills),
                    "Title": j.get("title"),
                    "Company": j.get("company"),
                    "Location": j.get("location"),
                    "Country": None,  # ✅ important change
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
            r = requests.get(
                "https://data.usajobs.gov/api/search",
                headers={
                    "User-Agent": st.secrets["USAJOBS_EMAIL"],
                    "Authorization-Key": st.secrets["USAJOBS_API_KEY"]
                },
                params={
                    "Keyword": skill,
                    "ResultsPerPage": 25
                },
                timeout=20
            )
    
            if r.status_code != 200:
                continue
    
            for j in r.json()["SearchResult"]["SearchResultItems"]:
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
