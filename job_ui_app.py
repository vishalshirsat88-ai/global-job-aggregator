import streamlit as st
import requests
import pandas as pd
import re
from datetime import datetime, timedelta

st.set_page_config(page_title="Global Job Aggregator", layout="wide")

# =========================================================
# 1. UI HEADER & CSS (Fixed Indentation Issue)
# =========================================================

st.markdown("""
<style>
/* ---------- GLOBAL BACKGROUND ---------- */
.stApp {
    background: linear-gradient(135deg, #f5f3ff 0%, #fdf2f8 50%, #fff7ed 100%);
}

/* ---------- SIDEBAR ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #6A5AE0, #B983FF);
    color: white;
}
section[data-testid="stSidebar"] * {
    color: white !important;
}

/* ---------- BUTTONS ---------- */
.stButton>button {
    background: linear-gradient(135deg, #FF5EDF, #FF8A00);
    color: white;
    border-radius: 14px;
    padding: 10px 20px;
    font-weight: 600;
    border: none;
    box-shadow: 0 8px 20px rgba(255, 94, 223, 0.35);
    transition: all 0.2s ease-in-out;
}
.stButton>button:hover {
    transform: translateY(-1px);
    box-shadow: 0 12px 28px rgba(255, 94, 223, 0.45);
}

/* ---------- INPUTS ---------- */
input, textarea {
    border-radius: 12px !important;
}

/* ---------- JOB CARD ---------- */
.job-card {
    background: rgba(255,255,255,0.9);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.08);
    margin-bottom: 20px;
    position: relative;
}
.job-title {
    font-size: 18px;
    font-weight: 700;
    color: #1F2937;
    margin-bottom: 4px;
}
.job-company {
    font-size: 14px;
    color: #6B7280;
    margin-bottom: 8px;
}
.job-location {
    font-size: 13px;
    color: #374151;
    margin-bottom: 10px;
}
.job-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 12px;
}
.apply-btn {
    background: linear-gradient(135deg, #FF5EDF, #FF8A00);
    color: white;
    padding: 8px 16px;
    border-radius: 12px;
    font-weight: 600;
    text-decoration: none;
    box-shadow: 0 8px 20px rgba(255, 94, 223, 0.35);
}
.apply-btn:hover { opacity: 0.9; }

/* ---------- BADGES ---------- */
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 6px;
}
.badge-remote { background: linear-gradient(135deg, #6A5AE0, #B983FF); color: white; }
.badge-hybrid { background: linear-gradient(135deg, #00C9A7, #92FE9D); color: #064E3B; }
.badge-onsite { background: #E5E7EB; color: #374151; }

/* ---------- DOWNLOAD BUTTON ---------- */
.download-btn button {
    background: linear-gradient(135deg, #00C9A7, #92FE9D) !important;
    color: #064E3B !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    padding: 10px 18px !important;
    box-shadow: 0 10px 25px rgba(0, 201, 167, 0.35) !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)

# FIXED HEADER INDENTATION HERE
st.markdown(
"""
<div style="display:flex; align-items:center; gap:14px; margin: 10px 0 25px 0;">
    <div style="background: linear-gradient(135deg, #6A5AE0, #B983FF); width:46px; height:46px; border-radius:14px; display:flex; align-items:center; justify-content:center; color:white; font-size:22px; font-weight:700;">
        MJ
    </div>
    <div>
        <div style="font-size:28px; font-weight:800; color:#1F2937; line-height:1.1;">
            Global Job Aggregator
        </div>
        <div style="font-size:13px; color:#6B7280; font-weight:500;">
            Search smarter. Apply faster.
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True
)

# =========================================================
# 2. CONFIG & HELPERS
# =========================================================
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_KEY", "")
JOOBLE_KEY   = st.secrets.get("JOOBLE_KEY", "")
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

def text_contains(text, items):
    if not items: return True
    t = (text or "").lower()
    return any(i.lower() in t for i in items)

def work_mode(text):
    t = (text or "").lower()
    if "remote" in t: return "Remote"
    if "hybrid" in t: return "Hybrid"
    return "On-site"

def city_match(city, text):
    if not city or not text: return False
    return city.lower() in text.lower()

def excel_link(url):
    return f'=HYPERLINK("{url}","Apply")' if url else ""

# =========================================================
# 3. DEBUGGABLE FETCHERS (NEW)
# =========================================================

def fetch_remote_jobs_debug(skills, level, posted_days):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)
    stats = {"found": 0, "dropped_level": 0, "dropped_date": 0}

    # 1. JSEARCH REMOTE
    for skill in skills:
        try:
            r = requests.get(
                "https://jsearch.p.rapidapi.com/search",
                headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "jsearch.p.rapidapi.com"},
                params={"query": f"{skill} remote job", "num_pages": 1},
                timeout=15
            )
            data = r.json().get("data", [])
            stats["found"] += len(data)

            for j in data:
                text_blob = f"{j.get('job_title','')} {j.get('job_description','')}"
                
                # Level Check
                if level and not text_contains(text_blob, [level]):
                    stats["dropped_level"] += 1
                    continue
                
                # Date Check
                dt = normalize_date(j.get("job_posted_at_datetime_utc",""))
                if dt and dt < cutoff:
                    stats["dropped_date"] += 1
                    continue

                rows.append({
                    "Source": "JSearch", "Skill": skill, "Title": j.get("job_title"),
                    "Company": j.get("employer_name"), "Location": "Remote",
                    "Country": "Remote", "Work Mode": "Remote",
                    "Posted": j.get("job_posted_at_datetime_utc",""),
                    "Apply": j.get("job_apply_link"), "_excel": excel_link(j.get("job_apply_link")),
                    "_date": dt
                })
        except: pass

    # 2. REMOTIVE
    try:
        r = requests.get(REMOTIVE_API, timeout=10).json()
        jobs = r.get("jobs", [])
        stats["found"] += len(jobs)
        for j in jobs:
            if not any(s.lower() in j.get("title","").lower() for s in skills):
                continue
            
            # Remotive doesn't always have strict dates or levels, we usually keep them
            # unless strict level matching is needed
            if level and not text_contains(j.get("title",""), [level]):
                stats["dropped_level"] += 1
                continue

            rows.append({
                "Source": "Remotive", "Skill": str(skills), "Title": j.get("title"),
                "Company": j.get("company_name"), "Location": "Remote",
                "Country": "Remote", "Work Mode": "Remote", "Posted": "",
                "Apply": j.get("url"), "_excel": excel_link(j.get("url")), "_date": None
            })
    except: pass

    return rows, stats

def fetch_jsearch_debug(skills, levels, countries, posted_days, cities=None):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)
    allowed_codes = {COUNTRIES[c].upper() for c in countries}
    stats = {"found": 0, "dropped_country": 0, "dropped_level": 0, "dropped_date": 0}

    for skill in skills:
        query = f"{skill} job"
        if cities: query += f" {cities[0]}"

        try:
            r = requests.get(
                "https://jsearch.p.rapidapi.com/search",
                headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "jsearch.p.rapidapi.com"},
                params={"query": query, "num_pages": 2}, # Try increasing num_pages if needed
                timeout=20
            )
            data = r.json().get("data", [])
            stats["found"] += len(data)

            for j in data:
                code = (j.get("job_country") or "").upper()
                if code not in allowed_codes:
                    stats["dropped_country"] += 1
                    continue

                text_blob = j.get("job_title","") + " " + j.get("job_description","")
                if levels and not text_contains(text_blob, levels):
                    stats["dropped_level"] += 1
                    continue

                dt = normalize_date(j.get("job_posted_at_datetime_utc",""))
                if dt and dt < cutoff:
                    stats["dropped_date"] += 1
                    continue

                rows.append({
                    "Source": "JSearch", "Skill": skill, "Title": j.get("job_title"),
                    "Company": j.get("employer_name"), "Location": j.get("job_city") or j.get("job_state") or code,
                    "Country": code, "Work Mode": work_mode(text_blob),
                    "Posted": j.get("job_posted_at_datetime_utc",""), "Apply": j.get("job_apply_link"),
                    "_excel": excel_link(j.get("job_apply_link")), "_date": dt
                })
        except: pass
    return rows, stats

def fetch_adzuna_debug(skills, levels, countries, posted_days, cities=None):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)
    stats = {"found": 0, "dropped_level": 0, "dropped_date": 0}

    for c in countries:
        try:
            r = requests.get(
                f"https://api.adzuna.com/v1/api/jobs/{COUNTRIES[c]}/search/1",
                params={
                    "app_id": ADZUNA_APP_ID, "app_key": ADZUNA_API_KEY,
                    "what": " ".join(skills), "where": cities[0] if cities else "",
                    "results_per_page": 20
                }, timeout=15
            ).json()
            data = r.get("results", [])
            stats["found"] += len(data)

            for j in data:
                text_blob = f"{j.get('title','')} {j.get('description','')}"
                if levels and not text_contains(text_blob, levels):
                    stats["dropped_level"] += 1
                    continue
                
                dt = normalize_date(j.get("created",""))
                if dt and dt < cutoff:
                    stats["dropped_date"] += 1
                    continue

                rows.append({
                    "Source": "Adzuna", "Skill": str(skills), "Title": j.get("title"),
                    "Company": j.get("company",{}).get("display_name"),
                    "Location": j.get("location",{}).get("display_name"),
                    "Country": c, "Work Mode": work_mode(j.get("title","")),
                    "Posted": j.get("created",""), "Apply": j.get("redirect_url"),
                    "_excel": excel_link(j.get("redirect_url")), "_date": dt
                })
        except: pass
    return rows, stats

def fetch_jooble_debug(skills, levels, countries, cities=None):
    rows = []
    stats = {"found": 0, "dropped_level": 0}
    for c in countries:
        try:
            r = requests.post(
                f"https://jooble.org/api/{JOOBLE_KEY}",
                json={"keywords": " ".join(skills), "location": cities[0] if cities else c},
                timeout=15
            ).json()
            data = r.get("jobs", [])
            stats["found"] += len(data)

            for j in data:
                if levels and not text_contains(j.get("title",""), levels):
                    stats["dropped_level"] += 1
                    continue
                
                rows.append({
                    "Source": "Jooble", "Skill": str(skills), "Title": j.get("title"),
                    "Company": j.get("company"), "Location": j.get("location"),
                    "Country": c, "Work Mode": work_mode(j.get("title","")),
                    "Posted": "", "Apply": j.get("link"),
                    "_excel": excel_link(j.get("link")), "_date": None
                })
        except: pass
    return rows, stats

# =========================================================
# 4. ENGINE
# =========================================================

def run_engine_debug(skills, levels, location, countries, posted_days):
    cities = [c.strip() for c in location.split(",") if c.strip()] if location else []
    
    # UI FOR DEBUGGING
    with st.expander("🕵️ API Stats (Click here if you see 0 results)", expanded=True):
        c1, c2, c3 = st.columns(3)
        
        # JSEARCH
        rows_js, stats_js = fetch_jsearch_debug(skills, levels, countries, posted_days, cities)
        c1.write("**JSearch**")
        c1.caption(f"Found: {stats_js['found']} | Level Drop: {stats_js['dropped_level']} | Date Drop: {stats_js['dropped_date']}")

        # ADZUNA
        rows_ad, stats_ad = fetch_adzuna_debug(skills, levels, countries, posted_days, cities)
        c2.write("**Adzuna**")
        c2.caption(f"Found: {stats_ad['found']} | Level Drop: {stats_ad['dropped_level']} | Date Drop: {stats_ad['dropped_date']}")

        # JOOBLE
        rows_jo, stats_jo = fetch_jooble_debug(skills, levels, countries, cities)
        c3.write("**Jooble**")
        c3.caption(f"Found: {stats_jo['found']} | Level Drop: {stats_jo['dropped_level']}")
    
    all_rows = rows_js + rows_ad + rows_jo
    if not all_rows: return pd.DataFrame(), False

    df = pd.DataFrame(all_rows).drop_duplicates(subset=["Title","Company","Location"])
    
    # City Match Logic
    if cities:
        mask = df["Location"].apply(lambda x: any(city_match(c, x) for c in cities))
        if mask.any():
            return df[mask], False
        else:
            return df, True # Fallback to country
    return df, False

# =========================================================
# 5. STREAMLIT UI INPUTS
# =========================================================

skills = [s.strip() for s in st.text_input("Skills (e.g. Software Engineer)", "Software Engineer").split(",") if s.strip()]
levels = [l.strip() for l in st.text_input("Levels (Leave empty for more results!)", "").split(",") if l.strip()]
location = st.text_input("Location (City or 'Remote')", "Mumbai")

is_remote = location.strip().lower() == "remote"

countries = st.multiselect("Country", list(COUNTRIES.keys()), default=["India"], disabled=is_remote)

if not is_remote and not countries:
    st.error("Country is mandatory unless location is Remote.")
    st.stop()

posted_days = st.slider("Posted within last X days", 1, 60, 14)

# =========================================================
# 6. ACTION & RESULTS
# =========================================================
col_run, col_toggle, col_download = st.columns([2, 3, 2])
with col_run: run_search = st.button("🚀 Run Job Search")
with col_toggle: classic_view = st.toggle("Classic View", value=False)
with col_download: download_placeholder = st.empty()

if run_search:
    with st.spinner("Fetching jobs..."):
        if is_remote:
            rows, stats = fetch_remote_jobs_debug(skills, levels[0] if levels else "", posted_days)
            df = pd.DataFrame(rows)
            fallback = False
            # Show remote stats
            with st.expander("Remote Stats", expanded=True):
                st.write(f"Found: {stats['found']} | Date Drop: {stats['dropped_date']} | Level Drop: {stats['dropped_level']}")
        else:
            df, fallback = run_engine_debug(skills, levels, location, countries, posted_days)

        if fallback:
            st.info(f"ℹ️ No exact matches for **{location}**. Showing jobs for the whole country instead.")
            
        if df.empty:
            st.warning("No jobs found. Try clearing the 'Levels' box or increasing 'Days'.")
        else:
            df = df.sort_values(by=["_date"], ascending=False, na_position="last")
            st.success(f"✅ Found {len(df)} jobs")
            
            # --- RENDER CARDS ---
            if not classic_view:
                cols = st.columns(2)
                for i, row in df.iterrows():
                    col = cols[i % 2]
                    badge_class = "badge-remote" if str(row["Work Mode"]).lower() == "remote" else "badge-onsite"
                    
                    card_html = f"""
                    <div class="job-card">
                      <div class="job-title">{row['Title']}</div>
                      <div class="job-company">{row['Company']}</div>
                      <div class="job-location">📍 {row['Location']}</div>
                      <span class="badge {badge_class}">{row['Work Mode']}</span>
                      <div class="job-actions">
                        <span class="badge badge-onsite">{row['Source']}</span>
                        <a class="apply-btn" href="{row['Apply']}" target="_blank">Apply →</a>
                      </div>
                    </div>
                    """
                    with col: st.markdown(card_html, unsafe_allow_html=True)
            else:
                st.dataframe(df.drop(columns=["_excel","_date"]), use_container_width=True, 
                             column_config={"Apply": st.column_config.LinkColumn("Apply Now")})

            # --- CSV EXPORT ---
            csv_df = df.copy()
            csv_df["Apply"] = csv_df["_excel"]
            csv_df = csv_df.drop(columns=["_excel","_date"])
            
            with col_download:
                st.markdown('<div class="download-btn">', unsafe_allow_html=True)
                download_placeholder.download_button("⬇️ Download CSV", csv_df.to_csv(index=False), "jobs.csv")
                st.markdown('</div>', unsafe_allow_html=True)
