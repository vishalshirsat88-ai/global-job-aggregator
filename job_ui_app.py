import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Global Job Aggregator", layout="wide")

# ---------- ORIGINAL CSS STYLES ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #f5f3ff 0%, #fdf2f8 50%, #fff7ed 100%);
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #6A5AE0, #B983FF);
    color: white;
}
.stButton>button {
    background: linear-gradient(135deg, #FF5EDF, #FF8A00);
    color: white;
    border-radius: 14px;
    padding: 10px 20px;
    font-weight: 600;
    border: none;
    box-shadow: 0 8px 20px rgba(255, 94, 223, 0.35);
}
.job-card {
    background: rgba(255,255,255,0.9);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}
.job-title { font-size: 18px; font-weight: 700; color: #1F2937; margin-bottom: 4px; }
.job-company { font-size: 14px; color: #6B7280; margin-bottom: 8px; }
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
    margin-right: 6px;
}
.badge-remote { background: linear-gradient(135deg, #6A5AE0, #B983FF); color: white; }
.badge-onsite { background: #E5E7EB; color: #374151; }
</style>
""", unsafe_allow_html=True)

# ---------- ORIGINAL HEADER ----------
st.markdown("""
<div style="display:flex; align-items:center; gap:14px; margin: 10px 0 25px 0;">
    <div style="background: linear-gradient(135deg, #6A5AE0, #B983FF); width:46px; height:46px; border-radius:14px; display:flex; align-items:center; justify-content:center; color:white; font-size:22px; font-weight:700;">MJ</div>
    <div>
        <div style="font-size:28px; font-weight:800; color:#1F2937; line-height:1.1;">Global Job Aggregator</div>
        <div style="font-size:13px; color:#6B7280;">Search smarter. Apply faster.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# CONFIG & HELPERS
# =========================================================
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_KEY", "")
ADZUNA_APP_ID = st.secrets.get("ADZUNA_APP_ID", "")
ADZUNA_API_KEY = st.secrets.get("ADZUNA_API_KEY", "")
REMOTIVE_API = "https://remotive.com/api/remote-jobs"

COUNTRIES = {
    "India": "in", "United States": "us", "United Kingdom": "gb",
    "United Arab Emirates": "ae", "Canada": "ca", "Australia": "au"
}

def normalize_date(val):
    try: return datetime.fromisoformat(str(val).replace("Z","").replace(".000",""))
    except: return None

def work_mode(text):
    t = (text or "").lower()
    if "remote" in t: return "Remote"
    if "hybrid" in t: return "Hybrid"
    return "On-site"

# =========================================================
# FETCHERS (INCLUDING REMOTIVE)
# =========================================================

def fetch_remotive(skills):
    rows = []
    try:
        r = requests.get(REMOTIVE_API, params={"search": " ".join(skills)}, timeout=15)
        data = r.json().get("jobs", [])
        for j in data:
            rows.append({
                "Source": "Remotive", "Title": j.get("title"),
                "Company": j.get("company_name"), "Location": "Remote",
                "Work Mode": "Remote", "Apply": j.get("url"),
                "_date": normalize_date(j.get("publication_date", ""))
            })
    except: pass
    return rows

def fetch_jsearch(skills, levels, countries, posted_days, location, is_remote):
    rows, stats = [], {"found": 0, "dropped": 0, "error": None}
    cutoff = datetime.utcnow() - timedelta(days=posted_days)
    
    for skill in skills:
        query = f"{skill} {' '.join(levels)}"
        if is_remote: query += " remote"
        
        params = {"query": query, "num_pages": 1}
        if not is_remote:
            params["location"] = location
            params["radius"] = 50 # Broaden for Navi Mumbai/Suburbs
            
        try:
            r = requests.get("https://jsearch.p.rapidapi.com/search",
                headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "jsearch.p.rapidapi.com"},
                params=params, timeout=20)
            data = r.json().get("data", [])
            stats["found"] += len(data)
            for j in data:
                dt = normalize_date(j.get("job_posted_at_datetime_utc",""))
                if dt and dt < cutoff:
                    stats["dropped"] += 1; continue
                rows.append({
                    "Source": j.get("job_publisher","JSearch"), "Title": j.get("job_title"),
                    "Company": j.get("employer_name"), "Location": f"{j.get('job_city', '')} {j.get('job_state', '')}".strip(),
                    "Work Mode": work_mode(j.get("job_title","") + " " + j.get("job_description","")),
                    "Apply": j.get("job_apply_link"), "_date": dt
                })
        except Exception as e: stats["error"] = str(e)
    return rows, stats

# =========================================================
# UI INPUTS
# =========================================================
skills = [s.strip() for s in st.text_input("Skills", "Software Engineer").split(",") if s.strip()]
levels = [l.strip() for l in st.text_input("Levels", "").split(",") if l.strip()]
location_input = st.text_input("Location (Type 'Remote' for global)", "Mumbai")

# REMOTE LOGIC: Gray out country if location is Remote
is_remote_mode = location_input.strip().lower() == "remote"
selected_countries = st.multiselect("Country Selection", options=list(COUNTRIES.keys()), 
                                    default=["India"], disabled=is_remote_mode)

posted_days = st.slider("Days Since Posted", 1, 60, 14)

col_run, col_toggle, col_download = st.columns([2, 3, 2])
with col_run: run_search = st.button("🚀 Run Job Search")
with col_toggle: classic_view = st.toggle("Classic View (Table)", value=False)
with col_download: download_placeholder = st.empty()

if run_search:
    all_jobs = []
    with st.spinner("🔍 Scanning global job markets..."):
        # 1. Fetch from JSearch (Universal)
        js_r, js_s = fetch_jsearch(skills, levels, selected_countries, posted_days, location_input, is_remote_mode)
        all_jobs += js_r
        
        # 2. If Remote, specifically add Remotive
        if is_remote_mode:
            all_jobs += fetch_remotive(skills)
            
        # DIAGNOSTIC HUB
        with st.expander("🕵️ Diagnostic Hub", expanded=True):
            st.write(f"**JSearch Status:** Raw Found: {js_s['found']} | Kept: {len(js_r)}")
            if is_remote_mode: st.write("**Remotive API:** Active (Global Remote)")
            if js_s['error']: st.error(js_s['error'])

        df = pd.DataFrame(all_jobs)
        if df.empty:
            st.warning("No jobs found. Try adjusting filters.")
        else:
            df = df.drop_duplicates(subset=["Title","Company","Location"])
            df = df.sort_values(by="_date", ascending=False, na_position="last")
            st.success(f"✅ Found {len(df)} jobs.")

            if not classic_view:
                grid = st.columns(2)
                for i, row in df.iterrows():
                    with grid[i % 2]:
                        mode_badge = "badge-remote" if row['Work Mode'] == "Remote" else "badge-onsite"
                        st.markdown(f"""
                        <div class="job-card">
                            <div class="job-title">{row['Title']}</div>
                            <div class="job-company">{row['Company']}</div>
                            <div class="job-location">📍 {row['Location']}</div>
                            <span class="badge {mode_badge}">{row['Work Mode']}</span>
                            <div style="margin-top:12px;"><a class="apply-btn" href="{row['Apply']}" target="_blank">Apply →</a></div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.dataframe(df.drop(columns=["_date"]), use_container_width=True)
            
            download_placeholder.download_button("⬇️ Download CSV", df.to_csv(index=False), "jobs.csv")
