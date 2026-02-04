import streamlit as st
import requests
import pandas as pd
import re
from datetime import datetime, timedelta

# --- CONFIG ---
st.set_page_config(page_title="TalentFlow | Job Aggregator", layout="wide")

# --- CUSTOM UI STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    .stApp {
        background-color: #030712;
        color: #f8fafc;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        z-index: -1;
        background: 
            radial-gradient(circle at 0% 0%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 100% 0%, rgba(236, 72, 153, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 50% 100%, rgba(139, 92, 246, 0.15) 0%, transparent 50%);
    }

    .hero-container {
        padding: 40px 0 30px 0;
        text-align: center;
    }
    .text-gradient {
        background: linear-gradient(to right, #818cf8, #f472b6, #fb923c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3.5rem;
        letter-spacing: -2px;
        margin: 0;
    }

    .search-console {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(40px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 1.5rem;
        padding: 2rem;
        margin-bottom: 2rem;
    }

    .job-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1.5rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .job-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-4px);
        background: rgba(255, 255, 255, 0.05);
    }
    .job-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #fff;
        margin-bottom: 0.4rem;
        line-height: 1.3;
    }
    .job-company {
        color: #818cf8;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 0.8rem;
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        margin-right: 4px;
        margin-bottom: 4px;
    }
    .badge-remote { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2); }
    .badge-hybrid { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.2); }
    .badge-onsite { background: rgba(255, 255, 255, 0.05); color: #94a3b8; border: 1px solid rgba(255, 255, 255, 0.1); }

    .apply-btn-modern {
        display: block;
        width: 100%;
        text-align: center;
        background: #fff;
        color: #030712;
        padding: 10px;
        border-radius: 0.8rem;
        font-weight: 700;
        text-decoration: none;
        margin-top: 1rem;
        font-size: 0.9rem;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: rgba(255,255,255,0.05) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- ENGINE SETTINGS ---
# Using .get() to avoid errors if keys are missing in secrets
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_KEY", "")
JOOBLE_KEY = st.secrets.get("JOOBLE_KEY", "")
ADZUNA_APP_ID = st.secrets.get("ADZUNA_APP_ID", "")
ADZUNA_API_KEY = st.secrets.get("ADZUNA_API_KEY", "")
REMOTIVE_API = "https://remotive.com/api/remote-jobs"

COUNTRIES = {
    "India": "in", "United States": "us", "United Kingdom": "gb", "UAE": "ae",
    "Canada": "ca", "Australia": "au", "Germany": "de", "France": "fr"
}

# --- HELPERS ---
def normalize_date(val):
    try: return datetime.fromisoformat(val.replace("Z","").replace(".000",""))
    except: return None

def skill_match(text, skill):
    return skill.lower() in (text or "").lower()

def work_mode(text):
    t = (text or "").lower()
    if "remote" in t: return "Remote"
    if "hybrid" in t: return "Hybrid"
    return "On-site"

def excel_link(url):
    return f'=HYPERLINK("{url}","Apply")' if url else ""

def city_match(row_location, search_locations):
    if not row_location: return False
    return any(loc.lower() in str(row_location).lower() for loc in search_locations)

# --- API FETCHERS ---
def fetch_remote_jobs(skills, level, posted_days):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)
    if RAPIDAPI_KEY:
        for skill in skills:
            try:
                r = requests.get("https://jsearch.p.rapidapi.com/search", headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "jsearch.p.rapidapi.com"}, params={"query": f"{skill} {level} remote job", "num_pages": 1}, timeout=15)
                if r.status_code == 200:
                    for j in r.json().get("data", []):
                        dt = normalize_date(j.get("job_posted_at_datetime_utc",""))
                        if dt and dt < cutoff: continue
                        rows.append({"Source": j.get("job_publisher",""), "Skill": skill, "Title": j.get("job_title"), "Company": j.get("employer_name"), "Location": "Remote", "Country": "Remote", "Work Mode": "Remote", "Posted": j.get("job_posted_at_datetime_utc",""), "Apply": j.get("job_apply_link"), "_date": dt, "_excel": excel_link(j.get("job_apply_link"))})
            except: pass
    try:
        r = requests.get(REMOTIVE_API, timeout=10).json()
        for skill in skills:
            for j in r.get("jobs", []):
                if skill_match(j.get("title",""), skill):
                    rows.append({"Source": "Remotive", "Skill": skill, "Title": j.get("title"), "Company": j.get("company_name"), "Location": "Remote", "Country": "Remote", "Work Mode": "Remote", "Posted": "", "Apply": j.get("url"), "_date": None, "_excel": excel_link(j.get("url"))})
    except: pass
    return rows

def fetch_adzuna(skills, levels, countries, posted_days, location):
    rows = []
    if not (ADZUNA_APP_ID and ADZUNA_API_KEY): return rows
    cutoff = datetime.utcnow() - timedelta(days=posted_days)
    for c in countries:
        try:
            r = requests.get(f"https://api.adzuna.com/v1/api/jobs/{COUNTRIES[c]}/search/1", params={"app_id": ADZUNA_APP_ID, "app_key": ADZUNA_API_KEY, "what": " OR ".join(skills + levels), "where": location or "", "results_per_page": 15}, timeout=10).json()
            for j in r.get("results", []):
                dt = normalize_date(j.get("created",""))
                if dt and dt < cutoff: continue
                rows.append({"Source": "Adzuna", "Skill": ", ".join(skills), "Title": j.get("title"), "Company": j.get("company",{}).get("display_name"), "Location": j.get("location",{}).get("display_name"), "Country": c, "Work Mode": work_mode(j.get("title","")), "Posted": j.get("created",""), "Apply": j.get("redirect_url"), "_date": dt, "_excel": excel_link(j.get("redirect_url"))})
        except: pass
    return rows

def fetch_jooble(skills, levels, countries, location):
    rows = []
    if not JOOBLE_KEY: return rows
    for c in countries:
        try:
            r = requests.post(f"https://jooble.org/api/{JOOBLE_KEY}", json={"keywords": " ".join(skills + levels), "location": location or c}, timeout=10).json()
            for j in r.get("jobs", []):
                rows.append({"Source": "Jooble", "Skill": ", ".join(skills), "Title": j.get("title"), "Company": j.get("company"), "Location": j.get("location"), "Country": None, "Work Mode": work_mode(j.get("title","")), "Posted": "", "Apply": j.get("link"), "_date": None, "_excel": excel_link(j.get("link"))})
        except: pass
    return rows

# --- MAIN APP UI ---
st.markdown("""
<div class="hero-container">
    <span style="letter-spacing: 2px; font-size: 10px; font-weight: 800; color: #6366f1; text-transform: uppercase;">Global Talent Aggregator</span>
    <h1 class="text-gradient">TalentFlow</h1>
</div>
""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="search-console">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        skill_input = st.text_input("Skills (comma separated)", "WFM")
    with c2:
        level_input = st.text_input("Levels", "Manager")
    with c3:
        loc_input = st.text_input("Location (or 'Remote')", "Berlin")
    
    c4, c5 = st.columns([3, 1])
    with c4:
        country_sel = st.multiselect("Countries", options=list(COUNTRIES.keys()), default=["Germany"])
    with c5:
        days_sel = st.slider("Days", 1, 30, 7)
    
    btn_col, toggle_col = st.columns([1, 1])
    with btn_col:
        run_search = st.button("🚀 RUN SEARCH", use_container_width=True)
    with toggle_col:
        classic_view = st.toggle("Classic View", False)
    st.markdown('</div>', unsafe_allow_html=True)

if run_search:
    skills = [s.strip() for s in skill_input.split(",") if s.strip()]
    levels = [l.strip() for l in level_input.split(",") if l.strip()]
    locations = [l.strip() for l in loc_input.split(",") if l.strip()]
    is_remote = loc_input.strip().lower() == "remote"

    with st.spinner("Scanning global databases..."):
        all_rows = []
        if is_remote:
            all_rows = fetch_remote_jobs(skills, levels[0] if levels else "", days_sel)
        else:
            for loc in locations:
                all_rows += fetch_adzuna(skills, levels, country_sel, days_sel, loc)
                all_rows += fetch_jooble(skills, levels, country_sel, loc)
        
        if not all_rows:
            st.info("No jobs found. (Note: Check if API keys are configured in Streamlit secrets)")
        else:
            df = pd.DataFrame(all_rows).drop_duplicates(subset=["Title", "Company", "Location"])
            
            # Post-fetch Filters
            if not is_remote and locations:
                df = df[df["Location"].apply(lambda x: city_match(x, locations))]
            
            if "_date" in df.columns:
                df = df.sort_values(by="_date", ascending=False, na_position="last")

            st.markdown(f"### Results ({len(df)})")
            
            if classic_view:
                st.dataframe(df.drop(columns=["_date", "_excel"]), use_container_width=True)
            else:
                cols = st.columns(3)
                for i, (_, row) in enumerate(df.iterrows()):
                    with cols[i % 3]:
                        mode = str(row['Work Mode']).lower()
                        badge = "badge-remote" if "remote" in mode else "badge-hybrid" if "hybrid" in mode else "badge-onsite"
                        st.markdown(f"""
                        <div class="job-card">
                            <div>
                                <div class="job-company">{row['Company'] or 'Private Company'}</div>
                                <div class="job-title">{row['Title']}</div>
                                <div style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 0.8rem;">📍 {row['Location']}</div>
                                <div class="badge {badge}">{row['Work Mode']}</div>
                                <div class="badge badge-onsite" style="opacity: 0.5">{row['Source']}</div>
                            </div>
                            <a href="{row['Apply']}" target="_blank" class="apply-btn-modern">Apply Now</a>
                        </div>
                        """, unsafe_allow_html=True)

            csv_data = df.copy()
            csv_data["Apply"] = csv_data["_excel"]
            st.download_button("Download CSV", csv_data.drop(columns=["_date", "_excel"]).to_csv(index=False), "jobs.csv")
