import os
import requests
import feedparser
from datetime import datetime, timedelta

RAPIDAPI_KEYS = [k.strip() for k in os.getenv("RAPIDAPI_KEYS", "").split(",") if k.strip()]
JOOBLE_KEY = os.getenv("JOOBLE_KEY")
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")
USAJOBS_EMAIL = os.getenv("USAJOBS_EMAIL")
USAJOBS_API_KEY = os.getenv("USAJOBS_API_KEY")

REMOTIVE_API = "https://remotive.com/api/remote-jobs"

current_key_index = 0

active_rapidapi_key = None


COUNTRIES = {
    "India": "in","United States": "us","United Kingdom": "gb",
    "United Arab Emirates": "ae","Canada": "ca","Australia": "au",
    "Germany": "de","France": "fr","Netherlands": "nl","Ireland": "ie",
    "Spain": "es","Italy": "it","Singapore": "sg","Brazil": "br",
    "South Africa": "za","Mexico": "mx","Poland": "pl","Belgium": "be",
    "Austria": "at","Switzerland": "ch"
}

from backend.utils.helpers import (
    normalize_date, parse_date, skill_match,
    work_mode, excel_link, expand_skill
)

# =========================================================
# KEY INITIALIZER
# =========================================================
if not RAPIDAPI_KEYS:
    print("⚠️ No RapidAPI keys configured")
    
def initialize_active_key():
    global active_rapidapi_key

    if active_rapidapi_key:
        return

    print("\n🔥 Initializing RapidAPI key cache...")

    for key in RAPIDAPI_KEYS:
        try:
            r = requests.get(
                "https://jsearch.p.rapidapi.com/search",
                headers={
                    "x-rapidapi-key": key,
                    "x-rapidapi-host": "jsearch.p.rapidapi.com"
                },
                params={"query": "test", "num_pages": 1},
                timeout=10
            )
            if r.status_code == 200:
                active_rapidapi_key = key
                print("✅ Cached working RapidAPI key:", key[:6] + "****")
                return
        except:
            continue

# =========================================================
# SAFE REQUEST ENGINE
# =========================================================
def safe_json_request(method, url, **kwargs):
    global current_key_index, active_rapidapi_key

    try:
        if "rapidapi" in url and RAPIDAPI_KEYS:

            # USE CACHED KEY FIRST
            if active_rapidapi_key:
                headers = kwargs.get("headers", {}).copy()
                headers["x-rapidapi-key"] = active_rapidapi_key
                headers["x-rapidapi-host"] = "jsearch.p.rapidapi.com"

                print("⚡ Using cached RapidAPI key")

                r = requests.request(method, url, timeout=10, headers=headers,
                                     **{k: v for k, v in kwargs.items() if k != "headers"})

                if 200 <= r.status_code < 300:
                    data = r.json()
                    if "data" in data:
                        print("✅ Jobs:", len(data.get("data", [])))
                    elif "results" in data:
                        print("✅ Jobs:", len(data.get("results", [])))
                    return data   # ← MISSING LINE
                else:
                    print("⚠️ Cached key expired → rotating")
                    active_rapidapi_key = None

            # 🔁 PROPER ROTATION
            total = len(RAPIDAPI_KEYS)

            for i in range(total):
                idx = (current_key_index + i) % total
                key = RAPIDAPI_KEYS[idx]

                headers = kwargs.get("headers", {}).copy()
                headers["x-rapidapi-key"] = key
                headers["x-rapidapi-host"] = "jsearch.p.rapidapi.com"

                print(f"\n🔑 Trying RapidAPI Key: {key[:6]}****")

                r = requests.request(method, url, timeout=10, headers=headers,
                                     **{k: v for k, v in kwargs.items() if k != "headers"})

                print("➡️ Status:", r.status_code)

                if 200 <= r.status_code < 300:
                    current_key_index = idx
                    active_rapidapi_key = key

                    data = r.json()
                    if "data" in data:
                        print("✅ Jobs:", len(data.get("data", [])))
                    elif "results" in data:
                        print("✅ Jobs:", len(data.get("results", [])))

                    return data

                if r.status_code in (403, 429):
                    continue

                break

            print("🚨 All RapidAPI keys exhausted")
            return {}

        # NON RAPIDAPI
        r = requests.request(method, url, timeout=10, **kwargs)
        return r.json() if 200 <= r.status_code < 300 else {}

    except Exception as e:
        print("❌ Request Failed:", e)
        return {}

# REMOTE FETCHERS
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
            dt = parse_date(j.get("job_posted_at_datetime_utc"))
            if dt and dt < cutoff:
                continue

            rows.append({
                "Source": j.get("job_publisher"),
                "API": "JSearch",
                "Skill": skill,
                "Title": j.get("job_title"),
                "Company": j.get("employer_name"),
                "Location": "Remote",
                "Country": "Remote",
                "Work Mode": "Remote",
                "Apply": j.get("job_apply_link"),
                "_excel": excel_link(j.get("job_apply_link")),
                "_date": dt
            })

    remotive = safe_json_request("GET", REMOTIVE_API)

    for skill in skills:
        for j in remotive.get("jobs", []):
            if skill_match(j.get("title"), skill):
                rows.append({
                    "Source": "Remotive",
                    "Skill": skill,
                    "Title": j.get("title"),
                    "Company": j.get("company_name"),
                    "Location": "Remote",
                    "Country": "Remote",
                    "Work Mode": "Remote",
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
                if skill.lower() in e.title.lower():
                    rows.append({
                        "Source":"WeWorkRemotely","Skill":skill,"Title":e.title,
                        "Location":"Remote","Country":"Remote","Apply":e.link,
                        "_excel":excel_link(e.link)
                    })

    return rows

def fetch_arbeitnow(skills):
    rows = []
    data = safe_json_request("GET", "https://www.arbeitnow.com/api/job-board-api")

    for j in data.get("data", []):
        for skill in skills:
            if skill_match(j.get("title"), skill):
                rows.append({
                    "Source": "Arbeitnow",
                    "Skill": skill,
                    "Title": j.get("title"),
                    "Company": j.get("company_name"),
                    "Location": j.get("location"),
                    "Apply": j.get("url"),
                    "_excel": excel_link(j.get("url"))
                })


    return rows

# =========================================================
#  STARTUP CALL
# =========================================================

def fetch_jsearch(skills, levels, countries, posted_days, location):

    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for skill in skills:
        for country in countries:

            query_parts = [skill]

            if levels:
                query_parts.append(" ".join(levels))

            if location:
                query_parts.append(location)
            else:
                query_parts.append(country)   # ← KEY LINE

            query = " ".join(query_parts)

            print(f"\n🚀 JSEARCH QUERY → {query}")

            data = safe_json_request(
                "GET",
                "https://jsearch.p.rapidapi.com/search",
                params={
                    "query": query,
                    "num_pages": 1
                }
            )

            for j in data.get("data", []):
                dt = normalize_date(j.get("job_posted_at_datetime_utc"))

                if dt and dt < cutoff:
                    continue

                rows.append({
                    "Source": j.get("job_publisher", ""),
                    "API": "JSearch",
                    "Skill": skill,
                    "Title": j.get("job_title"),
                    "Company": j.get("employer_name"),
                    "Location": j.get("job_city") or "",
                    "Country": (j.get("job_country") or "").upper(),
                    "Apply": j.get("job_apply_link"),
                    "_excel": excel_link(j.get("job_apply_link")),
                    "_date": dt
                })

    return rows


def fetch_adzuna(skills, levels, countries, posted_days, location):
    
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for c in countries:
        if c not in COUNTRIES: continue

        expanded = []
        for s in skills:
            expanded.extend(expand_skill(s))
        
        
        query = " OR ".join(set(expanded))



        print("\n===== ADZUNA DEBUG =====")
        print("Query:", query)
        print("Location:", location)
        print("Country:", c)
        print("========================\n")
        
        data = safe_json_request("GET",
            f"https://api.adzuna.com/v1/api/jobs/{COUNTRIES[c]}/search/1",
            params={
                "app_id": ADZUNA_APP_ID,
                "app_key": ADZUNA_API_KEY,
                "what": query,
                "where": location if location else c,
                "results_per_page": 20
            }
        )


        for j in data.get("results",[]):
            dt = normalize_date(j.get("created"))
            if dt and dt < cutoff: continue

            rows.append({
                "Source":"Adzuna","Skill":", ".join(skills),
                "API": "Adzuna",
                "Title":j.get("title"),"Company":j.get("company",{}).get("display_name"),
                "Location":j.get("location",{}).get("display_name"),
                "Country":c,"Apply":j.get("redirect_url"),
                "_excel":excel_link(j.get("redirect_url")),"_date":dt
            })
    return rows

def fetch_jooble(skills, levels, countries, location):

    rows = []

    for c in countries:

        expanded = []
        for s in skills:
            expanded.extend(expand_skill(s))
        
        keywords = " ".join(set(expanded))

        loc = f"{location}, {c}" if location else c

        print("\n===== JOOBLE DEBUG =====")
        print("Keywords:", keywords)
        print("Location:", loc)
        print("========================\n")

        data = safe_json_request(
            "POST",
            f"https://jooble.org/api/{JOOBLE_KEY}",
            json={
                "keywords": keywords,
                "location": loc
            }
        )


        for j in data.get("jobs",[]):
            rows.append({
                "Source":"Jooble","Skill":", ".join(skills),
                "API": "Jooble",
                "Title":j.get("title"),"Company":j.get("company"),
                "Location":j.get("location"),"Apply":j.get("link"),
                "_excel":excel_link(j.get("link"))
            })
    return rows

def fetch_usajobs(skills, posted_days):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for skill in skills:
        data = safe_json_request("GET","https://data.usajobs.gov/api/search",
            headers={"User-Agent":USAJOBS_EMAIL,"Authorization-Key":USAJOBS_API_KEY},
            params={"Keyword":skill})

        for j in data.get("SearchResult",{}).get("SearchResultItems",[]):
            d = j["MatchedObjectDescriptor"]
            dt = normalize_date(d.get("PublicationStartDate"))
            if dt and dt < cutoff: continue

            rows.append({
                "Source":"USAJobs","Skill":skill,"Title":d["PositionTitle"],
                "Company":d["OrganizationName"],
                "Location":", ".join(l["LocationName"] for l in d["PositionLocation"]),
                "Apply":d["PositionURI"],"_excel":excel_link(d["PositionURI"]),"_date":dt
            })
    return rows
    
# 🔥 PRELOAD WORKING RAPIDAPI KEY AT STARTUP
#initialize_active_key()
