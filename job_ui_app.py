import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Global Job Aggregator", layout="wide")

# ---------- CSS STYLES ----------
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
.job-title { font-size: 18px; font-weight: 700; color: #1F2937; }
.apply-btn {
    background: linear-gradient(135deg, #FF5EDF, #FF8A00);
    color: white;
    padding: 8px 16px;
    border-radius: 12px;
    font-weight: 600;
    text-decoration: none;
}
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 6px;
}
.badge-remote { background: #6A5AE0; color: white; }
.badge-onsite { background: #E5E7EB; color: #374151; }
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("""
<div style="display:flex; align-items:center; gap:14px; margin-bottom: 25px;">
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

# =========================================================
# FETCHERS: REMOVED STRICT FILTERS TO ALLOW SUBURBS
# =========================================================

def fetch_jsearch(skills, levels, countries, posted_days, location):
    rows, stats = [], {"found": 0, "dropped": 0, "error": None}
    cutoff = datetime.utcnow() - timedelta(days=posted_days)
    country_codes = [COUNTRIES[c].upper() for c in countries]
    
    for skill in skills:
        # NOTICE: We search for the skill/level, but let the API handle location separately
        search_query = f"{skill} {' '.join(levels)}".strip()
        try:
            r = requests.get(
                "https://jsearch.p.rapidapi.com/search",
                headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "jsearch.p.rapidapi.com"},
                params={
                    "query": search_query, 
                    "location": location, # API's location engine handles suburbs
                    "radius": 50,         # Search within 50km
                    "num_pages": 1
                }, timeout=20
            )
            data = r.json().get("data", [])
            stats["found"] += len(data)
            for j in data:
                j_country = (j.get("job_country") or "").upper()
                dt = normalize_date(j.get("job_posted_at_datetime_utc",""))
                if j_country not in country_codes or (dt and dt < cutoff):
                    stats["dropped"] += 1; continue
                rows.append({
                    "Source": j.get("job_publisher","JSearch"),
                    "Title": j.get("job_title"),
                    "Company": j.get("employer_name"),
                    "Location": f"{j.get('job_city', '')}, {j.get('job_state', '')}".strip(", "),
                    "Apply": j.get("job_apply_link"),
                    "_date": dt
                })
        except Exception as e: stats["error"] = str(e)
    return rows, stats

def fetch_adzuna(skills, levels, countries, posted_days, location):
    rows, stats = [], {"found": 0, "dropped": 0, "error": None}
    cutoff = datetime.utcnow() - timedelta(days=posted_days)
    for c in countries:
        try:
            r = requests.get(
                f"https://api.adzuna.com/v1/api/jobs/{COUNTRIES[c]}/search/1",
                params={
                    "app_id": ADZUNA_APP_ID, "app_key": ADZUNA_API_KEY,
                    "what": " ".join(skills + levels),
                    "where": location,
                    "distance": 30, # 30km radius
                    "results_per_page": 20
                }, timeout=15
            )
            data = r.json().get("results", [])
            stats["found"] += len(data)
            for j in data:
                dt = normalize_date(j.get("created",""))
                if dt and dt < cutoff: stats["dropped"] += 1; continue
                rows.append({
                    "Source": "Adzuna", "Title": j.get("title"),
                    "Company": j.get("company",{}).get("display_name"),
                    "Location": j.get("location",{}).get("display_name"),
                    "Apply": j.get("redirect_url"), "_date": dt
                })
        except Exception as e: stats["error"] = str(e)
    return rows, stats

# =========================================================
# UI & EXECUTION
# =========================================================
skills = [s.strip() for s in st.text_input("Skills", "Software Engineer").split(",") if s.strip()]
levels = [l.strip() for l in st.text_input("Levels", "").split(",") if l.strip()]
location = st.text_input("Location", "Mumbai")
countries = st.multiselect("Country", options=list(COUNTRIES.keys()), default=["India"])
posted_days = st.slider("Days Since Posted", 1, 60, 14)

col_run, col_toggle, col_download = st.columns([2, 3, 2])
with col_run: run_search = st.button("🚀 Run Job Search")
with col_toggle: classic_view = st.toggle("Classic View", value=False)
with col_download: download_placeholder = st.empty()

if run_search:
    with st.spinner(f"🔍 Searching {location} hub (including suburbs)..."):
        js_r, js_s = fetch_jsearch(skills, levels, countries, posted_days, location)
        ad_r, ad_s = fetch_adzuna(skills, levels, countries, posted_days, location)
        
        # Diagnostic Hub
        with st.expander("🕵️ Diagnostic Hub", expanded=True):
            c1, c2 = st.columns(2)
            c1.write(f"**JSearch:** Found {js_s['found']} | Kept {len(js_r)}")
            c2.write(f"**Adzuna:** Found {ad_s['found']} | Kept {len(ad_r)}")

        df = pd.DataFrame(js_r + ad_r)
        if not df.empty:
            df = df.drop_duplicates(subset=["Title","Company","Location"])
            df = df.sort_values(by="_date", ascending=False, na_position="last")
            
            if not classic_view:
                grid = st.columns(2)
                for i, row in df.iterrows():
                    with grid[i % 2]:
                        st.markdown(f"""
                        <div class="job-card">
                            <div class="job-title">{row['Title']}</div>
                            <div class="job-company">{row['Company']}</div>
                            <div class="job-location">📍 {row['Location']}</div>
                            <div style="margin-top:10px;"><a class="apply-btn" href="{row['Apply']}" target="_blank">Apply →</a></div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.dataframe(df, use_container_width=True)
            
            download_placeholder.download_button("⬇️ Download CSV", df.to_csv(index=False), "jobs.csv")
