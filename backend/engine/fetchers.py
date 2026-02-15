import os
import requests
import feedparser
from datetime import datetime, timedelta

RAPIDAPI_KEYS = os.getenv("RAPIDAPI_KEYS", "").split(",")
JOOBLE_KEY = os.getenv("JOOBLE_KEY")
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")
USAJOBS_EMAIL = os.getenv("USAJOBS_EMAIL")
USAJOBS_API_KEY = os.getenv("USAJOBS_API_KEY")

REMOTIVE_API = "https://remotive.com/api/remote-jobs"

# =========================
# STICKY KEY MEMORY
# =========================
current_key_index = 0

COUNTRIES = {
    "India": "in","United States": "us","United Kingdom": "gb",
    "United Arab Emirates": "ae","Canada": "ca","Australia": "au",
    "Germany": "de","France": "fr","Netherlands": "nl","Ireland": "ie",
    "Spain": "es","Italy": "it","Singapore": "sg","Brazil": "br",
    "South Africa": "za","Mexico": "mx","Poland": "pl","Belgium": "be",
    "Austria": "at","Switzerland": "ch"
}

from backend.utils.helpers import normalize_date, parse_date, skill_match, work_mode, excel_link

# =========================================================
# SAFE REQUEST WITH STICKY ROTATION
# =========================================================
def safe_json_request(method, url, **kwargs):
    global current_key_index

    try:
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

                print("➡️ Status:", r.status_code)

                if r.status_code == 200:
                    current_key_index = idx
                    data = r.json()
                    print("✅ Jobs:", len(data.get("data", [])))
                    return data

                if r.status_code in (403, 429):
                    print("⚠️ Key exhausted")
                    continue

            print("🚨 All RapidAPI keys exhausted")
            return {}

        r = requests.request(method, url, timeout=20, **kwargs)
        return r.json() if r.status_code == 200 else {}

    except Exception as e:
        print("❌ Request Failed:", e)
        return {}

# =========================================================
# REMOTE FETCHERS
# =========================================================
def fetch_remote_jobs(skills, level, posted_days):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for skill in skills:
        data = safe_json_request(
            "GET","https://jsearch.p.rapidapi.com/search",
            params={"query": f"{skill} {level} remote job","num_pages": 1}
        )

        for j in data.get("data", []):
            dt = parse_date(j.get("job_posted_at_datetime_utc"))
            if dt and dt < cutoff: continue

            rows.append({
                "Source": j.get("job_publisher"),
                "API": "JSearch",   # ← THIS IS MISSING NOW
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
            if skill_match(j.get("title",""), skill):
                rows.append({
                    "Source": "Remotive","Skill": skill,"Title": j.get("title"),
                    "Company": j.get("company_name"),"Location": "Remote",
                    "Country": "Remote","Work Mode": "Remote",
                    "Apply": j.get("url"),"_excel": excel_link(j.get("url")),"_date": None
                })
    return rows

# =========================================================
# RSS
# =========================================================
def fetch_weworkremotely(skills):
    rows = []
    feeds = ["https://weworkremotely.com/categories/remote-programming-jobs.rss"]

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
    data = safe_json_request("GET","https://www.arbeitnow.com/api/job-board-api")
    for j in data.get("data",[]):
        for skill in skills:
            if skill_match(j.get("title"),skill):
                rows.append({
                    "Source":"Arbeitnow","Skill":skill,"Title":j.get("title"),
                    "Company":j.get("company_name"),"Location":j.get("location"),
                    "Apply":j.get("url"),"_excel":excel_link(j.get("url"))
                })
    return rows

# =========================================================
# MAIN FETCHERS
# =========================================================
# =========================================================
# JSEARCH FETCHER — FINAL CLEAN VERSION
# =========================================================
def fetch_jsearch(skills, levels, countries, posted_days, location):

    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for skill in skills:
        
            # ---------------------------------
            # BUILD SEARCH QUERY (SMART LOGIC)
            # ---------------------------------
            query_parts = [skill]

            if levels:
            query_parts.append(" ".join(levels))
        
            # If city selected → include it
            if location:
                query_parts.append(location)
           
            query = " ".join(query_parts)

            print(f"\n🚀 JSEARCH DEBUG → Query: {query}")


            # ---------------------------------
            # API CALL
            # ---------------------------------
            data = safe_json_request(
                "GET",
                "https://jsearch.p.rapidapi.com/search",
                params={
                    "query": query,
                    "num_pages": 2,
                    "date_posted": "month"
                }
            )

            #raw_jobs = data.get("data", [])
            print("📦 Raw jobs fetched:", len(raw_jobs))

            # ---------------------------------
            # PARSE JOBS
            # ---------------------------------
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
                    "Location": j.get("job_city") or j.get("job_state") or "",
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

        data = safe_json_request("GET",
            f"https://api.adzuna.com/v1/api/jobs/{COUNTRIES[c]}/search/1",
            params={"app_id":ADZUNA_APP_ID,"app_key":ADZUNA_API_KEY,
                    "what":" OR ".join(skills),"where":location,"results_per_page":20})

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
        data = safe_json_request("POST",f"https://jooble.org/api/{JOOBLE_KEY}",
                                 json={"keywords":" ".join(skills),"location":location or c})

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
