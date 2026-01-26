import streamlit as st
import requests
import pandas as pd
import re
from datetime import datetime, timedelta

# =========================================================
# 1. PAGE CONFIG & STYLES
# =========================================================
st.set_page_config(page_title="Global Job Aggregator", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f3ff 0%, #fdf2f8 50%, #fff7ed 100%); }
    .job-card {
        background: rgba(255,255,255,0.9);
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #eee;
    }
    .job-title { font-size: 19px; font-weight: 700; color: #1F2937; margin-bottom: 4px; }
    .job-company { font-size: 15px; color: #4B5563; font-weight: 500; }
    .job-location { font-size: 13px; color: #6B7280; margin-top: 8px; }
    .apply-btn {
        background: linear-gradient(135deg, #6A5AE0, #B983FF);
        color: white !important;
        padding: 8px 20px;
        border-radius: 10px;
        text-decoration: none;
        font-weight: 600;
        display: inline-block;
        margin-top: 15px;
    }
    .badge {
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-remote { background: #EEF2FF; color: #4338CA; }
    .badge-onsite { background: #F3F4F6; color: #374151; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2. CORE UTILITIES
# =========================================================
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_KEY", "")
JOOBLE_KEY   = st.secrets.get("JOOBLE_KEY", "")
ADZUNA_APP_ID = st.secrets.get("ADZUNA_APP_ID", "")
ADZUNA_API_KEY = st.secrets.get("ADZUNA_API_KEY", "")

COUNTRIES = {
    "India": "in", "United States": "us", "United Kingdom": "gb",
    "United Arab Emirates": "ae", "Canada": "ca", "Australia": "au"
}

def normalize_date(val):
    try: return datetime.fromisoformat(str(val).replace("Z","").replace(".000",""))
    except: return None

def text_contains(text, items):
    if not items: return True
    t = (text or "").lower()
    return any(i.lower() in t for i in items)

def work_mode(text):
    t = (text or "").lower()
    if "remote" in t: return "Remote"
    if "hybrid" in t: return "Hybrid"
    return "On-site"

# =========================================================
# 3. GLOBAL FETCHERS (Optimized for Metropolitan Areas)
# =========================================================

def fetch_jsearch(skills, levels, countries, posted_days, city):
    rows = []
    stats = {"found": 0, "dropped_level": 0, "dropped_date": 0}
    cutoff = datetime.utcnow() - timedelta(days=posted_days)
    
    for skill in skills:
        # Build a smart query: e.g. "Software Engineer Manager in Mumbai"
        query = f"{skill} {' '.join(levels)} in {city}".strip()
        try:
            r = requests.get(
                "https://jsearch.p.rapidapi.com/search",
                headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "jsearch.p.rapidapi.com"},
                params={"query": query, "num_pages": 2},
                timeout=15
            )
            data = r.json().get("data", [])
            stats["found"] += len(data)

            for j in data:
                text_blob = f"{j.get('job_title','')} {j.get('job_description','')}"
                
                # We relax Level check if searching globally to avoid missing suburbs
                if levels and not text_contains(text_blob, levels):
                    stats["dropped_level"] += 1
                    continue
                
                dt = normalize_date(j.get("job_posted_at_datetime_utc",""))
                if dt and dt < cutoff:
                    stats["dropped_date"] += 1
                    continue

                rows.append({
                    "Source": j.get("job_publisher", "JSearch"),
                    "Title": j.get("job_title"),
                    "Company": j.get("employer_name"),
                    "Location": j.get("job_city") or j.get("job_state") or city,
                    "Mode": work_mode(text_blob),
                    "Apply": j.get("job_apply_link"),
                    "_date": dt
                })
        except: pass
    return rows, stats

def fetch_adzuna(skills, levels, countries, posted_days, city):
    rows = []
    stats = {"found": 0, "dropped_level": 0}
    for c in countries:
        try:
            r = requests.get(
                f"https://api.adzuna.com/v1/api/jobs/{COUNTRIES[c]}/search/1",
                params={
                    "app_id": ADZUNA_APP_ID, "app_key": ADZUNA_API_KEY,
                    "what": " ".join(skills + levels),
                    "where": city,
                    "results_per_page": 20
                }, timeout=15
            ).json()
            data = r.get("results", [])
            stats["found"] += len(data)
            for j in data:
                rows.append({
                    "Source": "Adzuna",
                    "Title": j.get("title"),
                    "Company": j.get("company",{}).get("display_name"),
                    "Location": j.get("location",{}).get("display_name"),
                    "Mode": work_mode(j.get("title","")),
                    "Apply": j.get("redirect_url"),
                    "_date": normalize_date(j.get("created",""))
                })
        except: pass
    return rows, stats

def fetch_jooble(skills, levels, countries, city):
    rows = []
    stats = {"found": 0}
    for c in countries:
        try:
            r = requests.post(
                f"https://jooble.org/api/{JOOBLE_KEY}",
                json={"keywords": " ".join(skills + levels), "location": city},
                timeout=15
            ).json()
            data = r.get("jobs", [])
            stats["found"] += len(data)
            for j in data:
                rows.append({
                    "Source": "Jooble",
                    "Title": j.get("title"),
                    "Company": j.get("company"),
                    "Location": j.get("location"),
                    "Mode": work_mode(j.get("title","")),
                    "Apply": j.get("link"),
                    "_date": None
                })
        except: pass
    return rows, stats

# =========================================================
# 4. GLOBAL ENGINE
# =========================================================

def run_global_engine(skills, levels, location, countries, posted_days):
    # If user types "Mumbai", the API handles "Navi Mumbai", "Thane", etc.
    with st.spinner(f"Searching global hubs for '{location}'..."):
        js_rows, js_stats = fetch_jsearch(skills, levels, countries, posted_days, location)
        ad_rows, ad_stats = fetch_adzuna(skills, levels, countries, posted_days, location)
        jo_rows, jo_stats = fetch_jooble(skills, levels, countries, location)

    # Debug Dashboard
    with st.expander("📊 Search Diagnostics"):
        c1, c2, c3 = st.columns(3)
        c1.metric("JSearch", len(js_rows), f"{js_stats['found']} raw")
        c2.metric("Adzuna", len(ad_rows), f"{ad_stats['found']} raw")
        c3.metric("Jooble", len(jo_rows), f"{jo_stats['found']} raw")
        st.caption("Note: 'Raw' counts show all results before level/date filters were applied.")

    all_jobs = js_rows + ad_rows + jo_rows
    if not all_jobs: return pd.DataFrame()

    df = pd.DataFrame(all_jobs).drop_duplicates(subset=["Title", "Company", "Location"])
    return df.sort_values(by="_date", ascending=False, na_position='last')

# =========================================================
# 5. UI LAYOUT
# =========================================================

st.title("🌍 Global Job Aggregator")
st.markdown("---")

with st.sidebar:
    st.header("Search Parameters")
    u_skills = [s.strip() for s in st.text_input("Skills", "Software Engineer").split(",") if s.strip()]
    u_levels = [l.strip() for l in st.text_input("Level (Manager, Lead, Senior)", "").split(",") if l.strip()]
    u_location = st.text_input("Location (City or Country)", "Mumbai")
    u_countries = st.multiselect("Active APIs for:", list(COUNTRIES.keys()), default=["India"])
    u_days = st.slider("Freshness (Days)", 1, 60, 14)
    search_clicked = st.button("🚀 Find Jobs", use_container_width=True)

if search_clicked:
    df = run_global_engine(u_skills, u_levels, u_location, u_countries, u_days)
    
    if df.empty:
        st.warning("No jobs found. Try removing the 'Level' filter or broadening your 'Location'.")
    else:
        st.success(f"Found {len(df)} jobs in the {u_location} region.")
        
        # Grid Display
        cols = st.columns(2)
        for i, row in df.iterrows():
            with cols[i % 2]:
                mode_class = "badge-remote" if row['Mode'] == "Remote" else "badge-onsite"
                st.markdown(f"""
                <div class="job-card">
                    <div class="job-title">{row['Title']}</div>
                    <div class="job-company">{row['Company']}</div>
                    <div class="job-location">📍 {row['Location']}</div>
                    <div style="margin-top:10px;">
                        <span class="badge {mode_class}">{row['Mode']}</span>
                        <span class="badge" style="background:#E0E7FF; color:#3730A3;">{row['Source']}</span>
                    </div>
                    <a href="{row['Apply']}" target="_blank" class="apply-btn">Apply Now →</a>
                </div>
                """, unsafe_allow_html=True)

        # Download
        st.download_button("📩 Download Results (CSV)", df.to_csv(index=False), "global_jobs.csv", "text/csv")
