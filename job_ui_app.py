import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Global Job Aggregator", layout="wide")

# ---------- ORIGINAL CSS STYLES ----------
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #f5f3ff 0%, #fdf2f8 50%, #fff7ed 100%); }
.job-card {
    background: rgba(255,255,255,0.9);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}
.job-title { font-size: 18px; font-weight: 700; color: #1F2937; margin-bottom: 4px; }
.apply-btn {
    background: linear-gradient(135deg, #FF5EDF, #FF8A00);
    color: white;
    padding: 8px 16px;
    border-radius: 12px;
    font-weight: 600;
    text-decoration: none;
    display: inline-block;
}
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}
.badge-remote { background: #6A5AE0; color: white; }
.badge-onsite { background: #E5E7EB; color: #374151; }
</style>
""", unsafe_allow_html=True)

# ---------- ORIGINAL HEADER ----------
st.markdown("""
<div style="display:flex; align-items:center; gap:14px; margin-bottom: 25px;">
    <div style="background: #6A5AE0; width:46px; height:46px; border-radius:14px; display:flex; align-items:center; justify-content:center; color:white; font-size:22px; font-weight:700;">MJ</div>
    <div>
        <div style="font-size:28px; font-weight:800; color:#1F2937;">Global Job Aggregator</div>
        <div style="font-size:13px; color:#6B7280;">Search smarter. Apply faster.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# CONFIG
# =========================================================
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_KEY", "")
JOOBLE_KEY   = st.secrets.get("JOOBLE_KEY", "")
ADZUNA_APP_ID = st.secrets.get("ADZUNA_APP_ID", "")
ADZUNA_API_KEY = st.secrets.get("ADZUNA_API_KEY", "")

COUNTRIES = {"India": "in", "United States": "us", "United Kingdom": "gb", "UAE": "ae", "Canada": "ca"}

def normalize_date(val):
    try: return datetime.fromisoformat(str(val).replace("Z","").replace(".000",""))
    except: return None

# =========================================================
# FETCHERS
# =========================================================

def fetch_jsearch(skills, levels, countries, posted_days, location, is_remote):
    rows, stats = [], {"found": 0, "error": None}
    cutoff = datetime.utcnow() - timedelta(days=posted_days)
    country_filter = [COUNTRIES[c].upper() for c in countries] if not is_remote else []
    
    for skill in skills:
        # Build query: "Software Engineer Manager Mumbai"
        q_loc = "remote" if is_remote else location
        query = f"{skill} {' '.join(levels)} {q_loc}".strip()
        
        try:
            r = requests.get("https://jsearch.p.rapidapi.com/search",
                headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "jsearch.p.rapidapi.com"},
                params={"query": query, "num_pages": 1}, timeout=15)
            data = r.json().get("data", [])
            stats["found"] += len(data)
            for j in data:
                dt = normalize_date(j.get("job_posted_at_datetime_utc",""))
                if not is_remote and j.get("job_country") not in country_filter: continue
                if dt and dt < cutoff: continue
                
                rows.append({
                    "Source": j.get("job_publisher","JSearch"), "Title": j.get("job_title"),
                    "Company": j.get("employer_name"), "Location": j.get("job_city") or j.get("job_country"),
                    "Work Mode": "Remote" if "remote" in (j.get("job_title","") + j.get("job_description","")).lower() else "On-site",
                    "Apply": j.get("job_apply_link"), "_date": dt
                })
        except Exception as e: stats["error"] = str(e)
    return rows, stats

def fetch_jooble(skills, levels, countries, location, is_remote):
    rows = []
    loc = "Remote" if is_remote else location
    # Jooble country-specific endpoints
    target_countries = countries if not is_remote else ["United States"] 
    for c in target_countries:
        try:
            r = requests.post(f"https://jooble.org/api/{JOOBLE_KEY}", 
                             json={"keywords": f"{' '.join(skills)} {' '.join(levels)}", "location": loc}, timeout=10)
            data = r.json().get("jobs", [])
            for j in data:
                rows.append({
                    "Source": "Jooble", "Title": j.get("title"), "Company": j.get("company"),
                    "Location": j.get("location"), "Work Mode": "Remote" if is_remote else "On-site",
                    "Apply": j.get("link"), "_date": None
                })
        except: pass
    return rows

def fetch_remotive(skills):
    rows = []
    try:
        r = requests.get("https://remotive.com/api/remote-jobs", params={"search": " ".join(skills)}, timeout=10)
        for j in r.json().get("jobs", []):
            rows.append({
                "Source": "Remotive", "Title": j.get("title"), "Company": j.get("company_name"),
                "Location": "Remote", "Work Mode": "Remote", "Apply": j.get("url"),
                "_date": normalize_date(j.get("publication_date"))
            })
    except: pass
    return rows

# =========================================================
# UI
# =========================================================
skills = [s.strip() for s in st.text_input("Skills", "Software Engineer").split(",") if s.strip()]
levels = [l.strip() for l in st.text_input("Levels", "").split(",") if l.strip()]
loc_input = st.text_input("Location", "Mumbai")

# REMOTE LOGIC
is_remote = loc_input.strip().lower() == "remote"
selected_countries = st.multiselect("Country Selection", options=list(COUNTRIES.keys()), 
                                    default=["India"], disabled=is_remote)

posted_days = st.slider("Days Since Posted", 1, 60, 14)

if st.button("🚀 Run Job Search"):
    with st.spinner("Searching..."):
        # Fetching
        js_r, js_s = fetch_jsearch(skills, levels, selected_countries, posted_days, loc_input, is_remote)
        jo_r = fetch_jooble(skills, levels, selected_countries, loc_input, is_remote)
        
        all_jobs = js_r + jo_r
        if is_remote:
            all_jobs += fetch_remotive(skills)
            
        # DIAGNOSTIC HUB (Restored)
        with st.expander("🕵️ Diagnostic Hub", expanded=True):
            st.write(f"**JSearch:** Found {js_s['found']} raw entries.")
            st.write(f"**Jooble:** Found {len(jo_r)} entries.")
            if is_remote: st.write("**Remotive:** Active")

        df = pd.DataFrame(all_jobs)
        if not df.empty:
            df = df.drop_duplicates(subset=["Title","Company"])
            st.success(f"Found {len(df)} jobs in {loc_input}")
            
            grid = st.columns(2)
            for i, row in df.iterrows():
                with grid[i % 2]:
                    badge = "badge-remote" if row['Work Mode'] == "Remote" else "badge-onsite"
                    st.markdown(f"""
                    <div class="job-card">
                        <div class="job-title">{row['Title']}</div>
                        <div class="job-company">{row['Company']}</div>
                        <div class="job-location">📍 {row['Location']}</div>
                        <span class="badge {badge}">{row['Work Mode']}</span>
                        <div style="margin-top:10px;"><a class="apply-btn" href="{row['Apply']}" target="_blank">Apply →</a></div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No jobs found for this region.")
