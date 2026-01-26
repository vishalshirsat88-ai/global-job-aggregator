import streamlit as st
import requests
import pandas as pd
import re
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
section[data-testid="stSidebar"] * {
    color: white !important;
}
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
</style>
""", unsafe_allow_html=True)

# ---------- ORIGINAL HEADER ----------
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
""", unsafe_allow_html=True)

# =========================================================
# API KEYS & HELPERS
# =========================================================
RAPIDAPI_KEY = st.secrets["RAPIDAPI_KEY"]
JOOBLE_KEY   = st.secrets["JOOBLE_KEY"]
ADZUNA_APP_ID = st.secrets["ADZUNA_APP_ID"]
ADZUNA_API_KEY = st.secrets["ADZUNA_API_KEY"]

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

def excel_link(url):
    return f'=HYPERLINK("{url}","Apply")' if url else ""

# =========================================================
# FETCHERS WITH BUILT-IN ERROR LOGGING
# =========================================================

def fetch_jsearch(skills, levels, countries, posted_days, location):
    rows = []
    stats = {"found": 0, "dropped": 0, "error": None}
    cutoff = datetime.utcnow() - timedelta(days=posted_days)
    allowed_codes = {COUNTRIES[c].upper() for c in countries}
    
    for skill in skills:
        query = f"{skill} {' '.join(levels)} in {location}".strip()
        try:
            r = requests.get(
                "https://jsearch.p.rapidapi.com/search",
                headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "jsearch.p.rapidapi.com"},
                params={"query": query, "num_pages": 1},
                timeout=20
            )
            if r.status_code != 200:
                stats["error"] = f"API Error: {r.status_code}"
                continue
                
            data = r.json().get("data", [])
            stats["found"] += len(data)

            for j in data:
                code = (j.get("job_country") or "").upper()
                dt = normalize_date(j.get("job_posted_at_datetime_utc",""))
                
                # Global relevance: we trust the API's query result, but keep country filter
                if code not in allowed_codes or (dt and dt < cutoff):
                    stats["dropped"] += 1
                    continue

                rows.append({
                    "Source": j.get("job_publisher","JSearch"),
                    "Title": j.get("job_title"),
                    "Company": j.get("employer_name"),
                    "Location": j.get("job_city") or j.get("job_state") or code,
                    "Country": code,
                    "Work Mode": work_mode(j.get("job_title","") + " " + j.get("job_description","")),
                    "Posted": j.get("job_posted_at_datetime_utc",""),
                    "Apply": j.get("job_apply_link"),
                    "_excel": excel_link(j.get("job_apply_link")),
                    "_date": dt
                })
        except Exception as e:
            stats["error"] = str(e)
    return rows, stats

def fetch_adzuna(skills, levels, countries, posted_days, location):
    rows = []
    stats = {"found": 0, "dropped": 0, "error": None}
    cutoff = datetime.utcnow() - timedelta(days=posted_days)
    for c in countries:
        try:
            r = requests.get(
                f"https://api.adzuna.com/v1/api/jobs/{COUNTRIES[c]}/search/1",
                params={
                    "app_id": ADZUNA_APP_ID, "app_key": ADZUNA_API_KEY,
                    "what": " ".join(skills + levels),
                    "where": location,
                    "results_per_page": 15
                }, timeout=15
            )
            if r.status_code != 200:
                stats["error"] = f"Error {r.status_code}"
                continue
            
            data = r.json().get("results", [])
            stats["found"] += len(data)
            for j in data:
                dt = normalize_date(j.get("created",""))
                if dt and dt < cutoff:
                    stats["dropped"] += 1
                    continue
                rows.append({
                    "Source": "Adzuna",
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
        except Exception as e:
            stats["error"] = str(e)
    return rows, stats

def fetch_jooble(skills, levels, countries, location):
    rows = []
    stats = {"found": 0, "error": None}
    for c in countries:
        try:
            r = requests.post(
                f"https://jooble.org/api/{JOOBLE_KEY}",
                json={"keywords": " ".join(skills + levels), "location": location},
                timeout=15
            )
            if r.status_code != 200:
                stats["error"] = f"Error {r.status_code}"
                continue
            data = r.json().get("jobs", [])
            stats["found"] += len(data)
            for j in data:
                rows.append({
                    "Source": "Jooble",
                    "Title": j.get("title"),
                    "Company": j.get("company"),
                    "Location": j.get("location"),
                    "Country": c,
                    "Work Mode": work_mode(j.get("title","")),
                    "Posted": "",
                    "Apply": j.get("link"),
                    "_excel": excel_link(j.get("link")),
                    "_date": None
                })
        except Exception as e:
            stats["error"] = str(e)
    return rows, stats

# =========================================================
# STREAMLIT UI INPUTS
# =========================================================
with st.sidebar:
    st.header("Search Filters")
    skills = [s.strip() for s in st.text_input("Skills", "Software Engineer").split(",") if s.strip()]
    levels = [l.strip() for l in st.text_input("Levels (e.g., Manager, Lead)", "").split(",") if l.strip()]
    location = st.text_input("City/Region (e.g., Mumbai, London)", "Mumbai")
    countries = st.multiselect("Target Countries", options=list(COUNTRIES.keys()), default=["India"])
    posted_days = st.slider("Days Since Posted", 1, 60, 14)
    run_search = st.button("🚀 Run Job Search", use_container_width=True)

col_toggle, col_download = st.columns([5, 2])
with col_toggle: classic_view = st.toggle("Classic View (Table)", value=False)
with col_download: download_placeholder = st.empty()

if run_search:
    with st.spinner(f"🔍 Searching globally for {location}..."):
        # Fetch data and stats
        js_rows, js_stats = fetch_jsearch(skills, levels, countries, posted_days, location)
        ad_rows, ad_stats = fetch_adzuna(skills, levels, countries, posted_days, location)
        jo_rows, jo_stats = fetch_jooble(skills, levels, countries, location)

        # ERROR LOGGER / DIAGNOSTIC HUB
        with st.expander("🕵️ Diagnostic Hub - Why am I seeing these results?", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**JSearch Status**")
                st.write(f"Raw Found: {js_stats['found']}")
                st.write(f"Filtered Out: {js_stats['dropped']}")
                if js_stats['error']: st.error(js_stats['error'])
            with c2:
                st.markdown("**Adzuna Status**")
                st.write(f"Raw Found: {ad_stats['found']}")
                st.write(f"Filtered Out: {ad_stats['dropped']}")
                if ad_stats['error']: st.error(ad_stats['error'])
            with c3:
                st.markdown("**Jooble Status**")
                st.write(f"Raw Found: {jo_stats['found']}")
                if jo_stats['error']: st.error(jo_stats['error'])

        df = pd.DataFrame(js_rows + ad_rows + jo_rows)
        
        if df.empty:
            st.warning("No jobs found. Try removing 'Levels' or widening your 'Location'.")
        else:
            df = df.drop_duplicates(subset=["Title","Company","Location","Source"])
            df = df.sort_values(by=["_date"], ascending=False, na_position="last")
            
            st.success(f"✅ Displaying {len(df)} unique jobs found.")

            if not classic_view:
                cols = st.columns(2)
                for i, row in df.iterrows():
                    col = cols[i % 2]
                    badge_class = "badge-onsite"
                    if str(row["Work Mode"]).lower() == "remote": badge_class = "badge-remote"
                    elif str(row["Work Mode"]).lower() == "hybrid": badge_class = "badge-hybrid"

                    card_html = f"""
                    <div class="job-card">
                      <div class="job-title">{row['Title']}</div>
                      <div class="job-company">{row['Company']}</div>
                      <div class="job-location">📍 {row['Location']}</div>
                      <span class="badge {badge_class}">{row['Work Mode']}</span>
                      <div class="job-actions">
                        <span class="badge badge-onsite" style="background:#E0E7FF; color:#3730A3;">{row['Source']}</span>
                        <a class="apply-btn" href="{row['Apply']}" target="_blank">Apply →</a>
                      </div>
                    </div>
                    """
                    with col: st.markdown(card_html, unsafe_allow_html=True)
            else:
                st.dataframe(df.drop(columns=["_excel","_date"]), use_container_width=True, 
                             column_config={"Apply": st.column_config.LinkColumn("Apply Now")})

            # CSV Export logic
            csv_df = df.copy()
            csv_df["Apply"] = csv_df["_excel"]
            csv_df = csv_df.drop(columns=["_excel","_date"])
            with col_download:
                download_placeholder.download_button("⬇️ Download CSV", csv_df.to_csv(index=False), "jobs.csv")
