import streamlit as st
import requests
import pandas as pd
import feedparser
from datetime import datetime, timedelta

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="Global Job Aggregator", layout="wide")

# =========================================================
# STYLES
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@600;700;800&display=swap');

.stApp {
    background: linear-gradient(135deg,#f5f3ff 0%,#fdf2f8 50%,#fff7ed 100%);
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#6A5AE0,#B983FF);
}
section[data-testid="stSidebar"] * {
    color: white !important;
}

/* BUTTONS */
.stButton>button {
    background: linear-gradient(135deg,#FF5EDF,#FF8A00);
    color:white;
    border-radius:14px;
    padding:10px 20px;
    font-weight:600;
    border:none;
    box-shadow:0 8px 20px rgba(255,94,223,0.35);
}

/* HERO */
.hero-title {
    display:inline-block;
    font-family:'Inter',sans-serif;
    font-size:52px;
    font-weight:800;
    letter-spacing:-1px;
    background:linear-gradient(90deg,#4F6CF7,#7A6FF0,#E8A06A);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}

.hero-subtitle {
    font-family:'Inter',sans-serif;
    font-size:18px;
    color:#475569;
    margin-top:14px;
}

/* JOB CARD */
.job-card {
    background:rgba(255,255,255,0.9);
    border-radius:18px;
    padding:18px;
    box-shadow:0 15px 35px rgba(0,0,0,0.08);
    margin-bottom:20px;
}
.job-title {font-size:18px;font-weight:700;color:#1F2937;}
.job-company {font-size:14px;color:#6B7280;}
.job-location {font-size:13px;color:#374151;}

.apply-btn {
    background:linear-gradient(135deg,#FF5EDF,#FF8A00);
    color:white;
    padding:8px 16px;
    border-radius:12px;
    text-decoration:none;
    font-weight:600;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO HEADER (MJ + TITLE)
# =========================================================
st.markdown("""
<div style="padding:80px 0 60px 0;display:flex;justify-content:center;">
  <div style="display:flex;align-items:center;gap:18px;">
    <div style="
        background:linear-gradient(135deg,#6A5AE0,#B983FF);
        width:56px;height:56px;border-radius:16px;
        display:flex;align-items:center;justify-content:center;
        color:white;font-size:24px;font-weight:800;
        font-family:'Inter',sans-serif;">
      MJ
    </div>
    <div>
      <div class="hero-title">Global Job Aggregator</div>
      <div class="hero-subtitle">Search smarter. Apply faster.</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SECRETS
# =========================================================
RAPIDAPI_KEY = st.secrets["RAPIDAPI_KEY"]
JOOBLE_KEY = st.secrets["JOOBLE_KEY"]
ADZUNA_APP_ID = st.secrets["ADZUNA_APP_ID"]
ADZUNA_API_KEY = st.secrets["ADZUNA_API_KEY"]
USAJOBS_EMAIL = st.secrets["USAJOBS_EMAIL"]
USAJOBS_KEY = st.secrets["USAJOBS_API_KEY"]

REMOTIVE_API = "https://remotive.com/api/remote-jobs"

COUNTRIES = {
    "India":"in",
    "United States":"us",
    "United Kingdom":"gb",
    "United Arab Emirates":"ae",
    "Canada":"ca",
    "Australia":"au"
}

# =========================================================
# HELPERS
# =========================================================
def excel_link(url):
    return f'=HYPERLINK("{url}","Apply")' if url else ""

def skill_match(text, skill):
    return skill.lower() in (text or "").lower()

# =========================================================
# EXISTING FETCHERS (UNCHANGED)
# =========================================================
def fetch_jsearch(skill, location):
    rows=[]
    r=requests.get(
        "https://jsearch.p.rapidapi.com/search",
        headers={"x-rapidapi-key":RAPIDAPI_KEY,"x-rapidapi-host":"jsearch.p.rapidapi.com"},
        params={"query":f"{skill} job {location}","num_pages":2},
        timeout=20
    )
    if r.status_code==200:
        for j in r.json().get("data",[]):
            rows.append({
                "Source":"JSearch",
                "Skill":skill,
                "Title":j.get("job_title"),
                "Company":j.get("employer_name"),
                "Location":j.get("job_city") or "",
                "Country":(j.get("job_country") or "").upper(),
                "Work Mode":"Remote" if "remote" in (j.get("job_description","").lower()) else "On-site",
                "Apply":j.get("job_apply_link"),
                "_excel":excel_link(j.get("job_apply_link"))
            })
    return rows

def fetch_adzuna(skill, location, countries):
    rows=[]
    for c in countries:
        r=requests.get(
            f"https://api.adzuna.com/v1/api/jobs/{COUNTRIES[c]}/search/1",
            params={
                "app_id":ADZUNA_APP_ID,
                "app_key":ADZUNA_API_KEY,
                "what":skill,
                "where":location,
                "results_per_page":20
            },timeout=15).json()
        for j in r.get("results",[]):
            rows.append({
                "Source":"Adzuna",
                "Skill":skill,
                "Title":j.get("title"),
                "Company":j.get("company",{}).get("display_name"),
                "Location":j.get("location",{}).get("display_name"),
                "Country":c,
                "Work Mode":"Remote" if "remote" in j.get("title","").lower() else "On-site",
                "Apply":j.get("redirect_url"),
                "_excel":excel_link(j.get("redirect_url"))
            })
    return rows

def fetch_jooble(skill, location, countries):
    rows=[]
    for c in countries:
        r=requests.post(
            f"https://jooble.org/api/{JOOBLE_KEY}",
            json={"keywords":skill,"location":location or c},
            timeout=15).json()
        for j in r.get("jobs",[]):
            rows.append({
                "Source":"Jooble",
                "Skill":skill,
                "Title":j.get("title"),
                "Company":j.get("company"),
                "Location":j.get("location"),
                "Country":None,
                "Work Mode":"On-site",
                "Apply":j.get("link"),
                "_excel":excel_link(j.get("link"))
            })
    return rows

def fetch_remotive(skills):
    rows=[]
    r=requests.get(REMOTIVE_API,timeout=15).json()
    for j in r.get("jobs",[]):
        for skill in skills:
            if skill_match(j["title"],skill):
                rows.append({
                    "Source":"Remotive",
                    "Skill":skill,
                    "Title":j["title"],
                    "Company":j["company_name"],
                    "Location":"Remote",
                    "Country":"Remote",
                    "Work Mode":"Remote",
                    "Apply":j["url"],
                    "_excel":excel_link(j["url"])
                })
    return rows

# =========================================================
# NEW FETCHERS
# =========================================================
def fetch_usajobs(skills):
    rows=[]
    for skill in skills:
        r=requests.get(
            "https://data.usajobs.gov/api/search",
            headers={"User-Agent":USAJOBS_EMAIL,"Authorization-Key":USAJOBS_KEY},
            params={"Keyword":skill,"ResultsPerPage":25},
            timeout=20)
        if r.status_code!=200: continue
        for j in r.json()["SearchResult"]["SearchResultItems"]:
            d=j["MatchedObjectDescriptor"]
            rows.append({
                "Source":"USAJobs",
                "Skill":skill,
                "Title":d["PositionTitle"],
                "Company":d["OrganizationName"],
                "Location":", ".join(l["LocationName"] for l in d["PositionLocation"]),
                "Country":"US",
                "Work Mode":"On-site",
                "Apply":d["PositionURI"],
                "_excel":excel_link(d["PositionURI"])
            })
    return rows

def fetch_arbeitnow(skills):
    rows=[]
    r=requests.get("https://www.arbeitnow.com/api/job-board-api",timeout=15)
    for j in r.json().get("data",[]):
        for skill in skills:
            if skill_match(j["title"],skill):
                rows.append({
                    "Source":"Arbeitnow",
                    "Skill":skill,
                    "Title":j["title"],
                    "Company":j["company_name"],
                    "Location":j["location"],
                    "Country":"EU",
                    "Work Mode":"Remote" if j["remote"] else "On-site",
                    "Apply":j["url"],
                    "_excel":excel_link(j["url"])
                })
    return rows

def fetch_wwr(skills):
    rows=[]
    feeds=[
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-management-jobs.rss"
    ]
    for f in feeds:
        feed=feedparser.parse(f)
        for e in feed.entries:
            for skill in skills:
                if skill_match(e.title,skill):
                    rows.append({
                        "Source":"WeWorkRemotely",
                        "Skill":skill,
                        "Title":e.title,
                        "Company":"",
                        "Location":"Remote",
                        "Country":"Remote",
                        "Work Mode":"Remote",
                        "Apply":e.link,
                        "_excel":excel_link(e.link)
                    })
    return rows

# =========================================================
# UI INPUTS
# =========================================================
skills=[s.strip() for s in st.text_input("Skills","Python").split(",") if s.strip()]
levels = [l.strip() for l in st.text_input("Level", "Manager").split(",") if l.strip()]
location=st.text_input("Location","")
countries=st.multiselect("Country",list(COUNTRIES.keys()),default=["India"])

if st.button("🚀 Run Job Search"):
    with st.spinner("Fetching jobs..."):
        rows=[]
        for skill in skills:
            rows+=fetch_jsearch(skill,location)
            rows+=fetch_adzuna(skill,location,countries)
            rows+=fetch_jooble(skill,location,countries)
        rows+=fetch_remotive(skills)
        rows+=fetch_usajobs(skills)
        rows+=fetch_arbeitnow(skills)
        rows+=fetch_wwr(skills)

        df=pd.DataFrame(rows).drop_duplicates(
            subset=["Title","Company","Location","Source"]
        )

        if df.empty:
            st.warning("No jobs found.")
        else:
            st.success(f"✅ Found {len(df)} jobs")
            st.markdown("### 🧾 Job Results")

            cols = st.columns(2, gap="large")
            
            for i, row in df.iterrows():
                card_html = f"""
                <div class="job-card">
                    <div class="job-title">{row['Title']}</div>
                    <div class="job-company">{row['Company']}</div>
                    <div class="job-location">📍 {row['Location']}</div>
            
                    <div style="margin-top:12px; display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:12px; color:#6B7280;">{row['Skill']}</span>
                        <a class="apply-btn" href="{row['Apply']}" target="_blank">Apply →</a>
                    </div>
                </div>
                """
            
                with cols[i % 2]:
                    st.markdown(card_html, unsafe_allow_html=True)



