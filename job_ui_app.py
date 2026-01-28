import streamlit as st
import requests
import pandas as pd
import re
from datetime import datetime, timedelta

st.set_page_config(page_title="Global Job Aggregator", layout="wide")

# force redeploy


st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@600;700;800&display=swap');

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

/* ---------- DATAFRAME (TEMP) ---------- */
div[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 12px 30px rgba(0,0,0,0.08);
}

/* ---------- BADGES ---------- */
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 6px;
}
.badge-remote {
    background: linear-gradient(135deg, #6A5AE0, #B983FF);
    color: white;
}
.badge-hybrid {
    background: linear-gradient(135deg, #00C9A7, #92FE9D);
    color: #064E3B;
}
.badge-onsite {
    background: #E5E7EB;
    color: #374151;
}

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
.download-btn button:hover {
    transform: translateY(-1px);
    box-shadow: 0 14px 32px rgba(0, 201, 167, 0.45) !important;
}


</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.hero-title {
    font-family: 'Inter', sans-serif;
    font-size: 52px;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -1px;
    background: linear-gradient(
        90deg,
        #4F6CF7 0%,
        #7A6FF0 50%,
        #E8A06A 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 18px;
    color: #475569;
    margin-top: 14px;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="padding: 80px 0 60px 0; text-align:center;">
    <div class="hero-title">
        Global Job Aggregator
    </div>
    <div class="hero-subtitle">
        Search smarter. Apply faster.
    </div>
</div>
""", unsafe_allow_html=True)


st.markdown("""
<style>

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

.apply-btn:hover {
    opacity: 0.9;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# API KEYS
# =========================================================
RAPIDAPI_KEY = st.secrets["RAPIDAPI_KEY"]
JOOBLE_KEY   = st.secrets["JOOBLE_KEY"]
ADZUNA_APP_ID = st.secrets["ADZUNA_APP_ID"]
ADZUNA_API_KEY = st.secrets["ADZUNA_API_KEY"]
REMOTIVE_API = "https://remotive.com/api/remote-jobs"

# =========================================================
# COUNTRY MAP
# =========================================================
COUNTRIES = {
    "India": "in",
    "United States": "us",
    "United Kingdom": "gb",
    "United Arab Emirates": "ae",
    "Canada": "ca",
    "Australia": "au",
    "Germany": "de",
    "France": "fr",
    "Netherlands": "nl",
    "Ireland": "ie",
    "Spain": "es",
    "Italy": "it"
}

# =========================================================
# HELPERS
# =========================================================
def normalize_date(val):
    try:
        return datetime.fromisoformat(val.replace("Z","").replace(".000",""))
    except:
        return None

def parse_date(val):
    try:
        return datetime.fromisoformat(val.replace("Z","").replace(".000",""))
    except:
        return None

def skill_match(text, skill):
    if not text or not skill:
        return False
    return skill.lower() in text.lower()


def work_mode(text):
    t = (text or "").lower()
    if "remote" in t:
        return "Remote"
    if "hybrid" in t:
        return "Hybrid"
    return "On-site"


def excel_link(url):
    return f'=HYPERLINK("{url}","Apply")' if url else ""

def city_match(row_location, search_locations):
    if not row_location:
        return False
    row_loc = row_location.lower()
    return any(loc.lower() in row_loc for loc in search_locations)


# =========================================================
# REMOTE SEARCH
# =========================================================
def fetch_remote_jobs(skills, level, posted_days):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for skill in skills:
        r = requests.get(
            "https://jsearch.p.rapidapi.com/search",
            headers={
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": "jsearch.p.rapidapi.com"
            },
            params={
                "query": f"{skill} {level} remote job",
                "num_pages": 1
            },
            timeout=20
        )

        if r.status_code == 200:
            for j in r.json().get("data", []):
                blob = f"{j.get('job_title','')} {j.get('job_description','')}"
                if not skill_match(blob, skill):
                    continue

                dt = parse_date(j.get("job_posted_at_datetime_utc",""))
                if dt and dt < cutoff:
                    continue

                rows.append({
                    "Source": j.get("job_publisher",""),
                    "Skill": skill,
                    "Title": j.get("job_title"),
                    "Company": j.get("employer_name"),
                    "Location": "Remote",
                    "Country": "Remote",
                    "Work Mode": "Remote",
                    "Posted": j.get("job_posted_at_datetime_utc",""),
                    "Apply": j.get("job_apply_link"),
                    "_excel": excel_link(j.get("job_apply_link")),
                    "_date": dt
                })

    r = requests.get(REMOTIVE_API, timeout=15).json()
    for skill in skills:
        for j in r.get("jobs", []):
            if not skill_match(j.get("title",""), skill):
                continue

            rows.append({
                "Source": "Remotive",
                "Skill": skill,
                "Title": j.get("title"),
                "Company": j.get("company_name"),
                "Location": "Remote",
                "Country": "Remote",
                "Work Mode": "Remote",
                "Posted": "",
                "Apply": j.get("url"),
                "_excel": excel_link(j.get("url")),
                "_date": None
            })

    return rows

# =========================================================
# NON-REMOTE FETCHERS
# =========================================================
def fetch_jsearch(skills, levels, countries, posted_days, location):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for skill in skills:
        query = f"{skill} job {location}".strip()

        r = requests.get(
            "https://jsearch.p.rapidapi.com/search",
            headers={
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": "jsearch.p.rapidapi.com"
            },
            params={
                "query": query,
                "num_pages": 2
            },
            timeout=20
        )

        if r.status_code != 200:
            continue

        for j in r.json().get("data", []):
            dt = normalize_date(j.get("job_posted_at_datetime_utc",""))
            if dt and dt < cutoff:
                continue

            rows.append({
                "Source": j.get("job_publisher",""),
                "Skill": skill,
                "Title": j.get("job_title"),
                "Company": j.get("employer_name"),
                "Location": j.get("job_city") or j.get("job_state") or "",
                "Country": (j.get("job_country") or "").upper(),
                "Work Mode": work_mode(j.get("job_description","")),
                "Posted": j.get("job_posted_at_datetime_utc",""),
                "Apply": j.get("job_apply_link"),
                "_excel": excel_link(j.get("job_apply_link")),
                "_date": dt
            })

    return rows



def fetch_adzuna(skills, levels, countries, posted_days, location):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for c in countries:
        r = requests.get(
            f"https://api.adzuna.com/v1/api/jobs/{COUNTRIES[c]}/search/1",
            params={
                "app_id": ADZUNA_APP_ID,
                "app_key": ADZUNA_API_KEY,
                "what": " OR ".join(skills + levels),
              "where": location or "",   # let Adzuna search country-wide  # ✅ CITY USED
                "results_per_page": 20
            },
            timeout=15
        ).json()

        for j in r.get("results", []):
            dt = normalize_date(j.get("created",""))
            if dt and dt < cutoff:
                continue

            rows.append({
                "Source": "Adzuna",
                "Skill": ", ".join(skills),
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

    return rows


def fetch_jooble(skills, levels, countries, location):
    rows = []

    for c in countries:
        r = requests.post(
            f"https://jooble.org/api/{JOOBLE_KEY}",
            json={
                "keywords": " ".join(skills + levels),
                "location": location or c   # country-level search only
            },
            timeout=15
        ).json()

        for j in r.get("jobs", []):
            rows.append({
                "Source": "Jooble",
                "Skill": ", ".join(skills),
                "Title": j.get("title"),
                "Company": j.get("company"),
                "Location": j.get("location"),
                "Country": None,  # ✅ important change
                "Work Mode": work_mode(j.get("title","")),
                "Posted": "",
                "Apply": j.get("link"),
                "_excel": excel_link(j.get("link")),
                "_date": None
            })

    return rows

def fetch_usajobs(skills, posted_days):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for skill in skills:
        r = requests.get(
            "https://data.usajobs.gov/api/search",
            headers={
                "User-Agent": st.secrets["USAJOBS_EMAIL"],
                "Authorization-Key": st.secrets["USAJOBS_API_KEY"]
            },
            params={
                "Keyword": skill,
                "ResultsPerPage": 25
            },
            timeout=20
        )

        if r.status_code != 200:
            continue

        for j in r.json()["SearchResult"]["SearchResultItems"]:
            d = j["MatchedObjectDescriptor"]

            rows.append({
                "Source": "USAJobs",
                "Skill": skill,
                "Title": d["PositionTitle"],
                "Company": d["OrganizationName"],
                "Location": ", ".join(
                    l["LocationName"] for l in d.get("PositionLocation", [])
                ),
                "Country": "US",
                "Work Mode": "On-site",
                "Posted": d.get("PublicationStartDate", ""),
                "Apply": d["PositionURI"],
                "_excel": excel_link(d["PositionURI"]),
                "_date": normalize_date(d.get("PublicationStartDate", ""))
            })

    return rows


def fetch_arbeitnow(skills):
    rows = []
    r = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=15)

    if r.status_code != 200:
        return rows

    for j in r.json().get("data", []):
        for skill in skills:
            if not skill_match(j.get("title", ""), skill):
                continue

            rows.append({
                "Source": "Arbeitnow",
                "Skill": skill,
                "Title": j.get("title"),
                "Company": j.get("company_name"),
                "Location": j.get("location"),
                "Country": "EU",
                "Work Mode": "Remote" if j.get("remote") else "On-site",
                "Posted": "",
                "Apply": j.get("url"),
                "_excel": excel_link(j.get("url")),
                "_date": None
            })

    return rows

import feedparser

def fetch_weworkremotely(skills):
    rows = []
    feeds = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-management-jobs.rss"
    ]

    for feed_url in feeds:
        feed = feedparser.parse(feed_url)

        for e in feed.entries:
            for skill in skills:
                if not skill_match(e.title, skill):
                    continue

                rows.append({
                    "Source": "WeWorkRemotely",
                    "Skill": skill,
                    "Title": e.title,
                    "Company": "",
                    "Location": "Remote",
                    "Country": "Remote",
                    "Work Mode": "Remote",
                    "Posted": "",
                    "Apply": e.link,
                    "_excel": excel_link(e.link),
                    "_date": None
                })

    return rows


# =========================================================
# ENGINE (MULTI-SKILL + MULTI-CITY LOGIC)
# =========================================================
def run_engine(skills, levels, locations, countries, posted_days):
    all_rows = []

    for loc in locations:
        for skill in skills:
            all_rows += fetch_jsearch([skill], levels, countries, posted_days, loc)
            all_rows += fetch_adzuna([skill], levels, countries, posted_days, loc)
            all_rows += fetch_jooble([skill], levels, countries, loc)

    if not all_rows:
        return pd.DataFrame(), True

    df = pd.DataFrame(all_rows)

    # -----------------------------
    # COUNTRY FILTER ONLY
    # -----------------------------
    allowed_country_names = {c.upper() for c in countries}

    if "Country" in df.columns:
        df = df[
            df["Country"].isna() |
            (df["Country"].str.upper() == "REMOTE") |
            (df["Country"].str.upper() == "EU") |   # ✅ allow Arbeitnow
            df["Country"].str.upper().isin(allowed_country_names)
        ]


    if df.empty:
        return pd.DataFrame(), True

    # Deduplicate across locations
    df = df.drop_duplicates(
        subset=["Title", "Company", "Location", "Source"]
    )

    return df, False





# =========================================================
# STREAMLIT UI
# =========================================================


skills = [s.strip() for s in st.text_input("Skills", "WFM").split(",") if s.strip()]
levels = [l.strip() for l in st.text_input("Levels", "Manager").split(",") if l.strip()]
location = st.text_input("Location (city or Remote, comma separated)", "")
locations = [l.strip() for l in location.split(",") if l.strip()]
is_remote = location.strip().lower() == "remote"



countries = st.multiselect(
    "Country",
    options=list(COUNTRIES.keys()),
    default=["India"],
    disabled=is_remote
)

is_us_search = (
    "United States" in countries or
    location.strip().lower() in ["usa", "united states","america"]
)

if not is_remote and not countries:
    st.error("Country is mandatory unless location is Remote.")
    st.stop()

posted_days = st.slider("Posted within last X days", 1, 60, 7)


# =========================
# TOP ACTION BAR
# =========================
col_run, col_toggle, col_download = st.columns([2, 3, 2])

with col_run:
    run_search = st.button("🚀 Run Job Search")

with col_toggle:
    classic_view = st.toggle("Classic View", value=False)


with col_download:
    download_placeholder = st.empty()


if run_search:
    with st.spinner("Fetching jobs..."):
        if is_remote:
            rows = fetch_remote_jobs(skills, levels[0] if levels else "", posted_days)
        
            # ➕ append new remote-safe sources
            rows += fetch_arbeitnow(skills)
            rows += fetch_weworkremotely(skills)
        
            df = pd.DataFrame(rows)
            fallback = False
        
        else:
            df, fallback = run_engine(skills, levels, locations, countries, posted_days)
        
            # ➕ append country-safe sources
            extra_rows = []
            if is_us_search:
                extra_rows += fetch_usajobs(skills, posted_days)
            
            # EU-only source – safe to always append
            if any(c in ["Germany","France","Netherlands","Ireland","Spain","Italy"] for c in countries):
                extra_rows += fetch_arbeitnow(skills)

            
            if not df.empty and extra_rows:
                df = pd.concat([df, pd.DataFrame(extra_rows)], ignore_index=True)


        
            # 🔁 COUNTRY-LEVEL FALLBACK
            if fallback:
                df, _ = run_engine(
                    skills,
                    levels,
                    locations=[""],   #⬅️ country-only search
                    countries=countries,
                    posted_days=posted_days
                )


        if fallback:
             st.info(
                f"ℹ️ No jobs found for **{location}**. "
                f"Showing country-level jobs instead."
            )
            
        if df.empty:
            st.warning("No jobs found.")
        else:
            # ---------------------------------------
            # 🔒 FINAL CITY-LEVEL GUARD (NON-REMOTE)
            # ---------------------------------------
            if not is_remote and locations:
                df = df[
                    df["Location"].apply(
                        lambda x: city_match(str(x), locations)
                    )
                ]
        
            if df.empty:
                st.warning("No jobs found after location filter.")
                st.stop()
        
            # ✅ ALWAYS sort AFTER filtering
            df = df.sort_values(by=["_date"], ascending=False, na_position="last")
        
            st.success(f"✅ Found {len(df)} jobs")

    
            # =========================
            # VIEW MODE TOGGLE
            # =========================
            if not classic_view:
                cols = st.columns(2)
    
                for i, row in df.iterrows():
                    col = cols[i % 2]
    
                    badge_class = "badge-onsite"
                    if str(row["Work Mode"]).lower() == "remote":
                        badge_class = "badge-remote"
                    elif str(row["Work Mode"]).lower() == "hybrid":
                        badge_class = "badge-hybrid"
    
                    card_html = f"""
    <div class="job-card">
      <div class="job-title">{row['Title']}</div>
      <div class="job-company">{row['Company']}</div>
      <div class="job-location">📍 {row['Location']}</div>
    
      <span class="badge {badge_class}">
        {row['Work Mode']}
      </span>
    
      <div class="job-actions">
        <span class="badge badge-onsite">{row['Skill']}</span>
        <a class="apply-btn" href="{row['Apply']}" target="_blank">
          Apply →
        </a>
      </div>
    </div>
    """
                    with col:
                        st.markdown(card_html, unsafe_allow_html=True)
    
            else:
                # =========================
                # CLASSIC TABLE VIEW
                # =========================
                st.dataframe(
                    df.drop(columns=["_excel","_date"]),
                    use_container_width=True,
                    column_config={
                        "Apply": st.column_config.LinkColumn("Apply Now")
                    }
                )


    
            # =========================
            # CSV EXPORT (COMMON)
            # =========================
            csv_df = df.copy()
            csv_df["Apply"] = csv_df["_excel"]
            csv_df = csv_df.drop(columns=["_excel","_date"])
    
            with col_download:
                st.markdown('<div class="download-btn">', unsafe_allow_html=True)
                download_placeholder.download_button(
                    "⬇️ Download CSV",
                    csv_df.to_csv(index=False),
                    "job_results.csv"
                )
                st.markdown('</div>', unsafe_allow_html=True)

            # =========================================================
            # 🔍 API RESPONSE SUMMARY (DEBUG PANEL)
            # =========================================================
            st.markdown("---")
            st.markdown("### 🔎 API Response Summary")
            
            if not df.empty and "Source" in df.columns:
                summary = (
                    df.groupby("Source")
                    .size()
                    .reset_index(name="Jobs Returned")
                    .sort_values("Jobs Returned", ascending=False)
                )
            
                st.dataframe(
                    summary,
                    use_container_width=True
                )
            else:
                st.info("No jobs available to summarize.")
            
            # ---------------------------------------------------------
            # 🔍 Arbeitnow Deep Debug (Germany / EU visibility)
            # ---------------------------------------------------------
            if run_search and not is_remote:
                arbeitnow_raw = fetch_arbeitnow(skills)
            
                if arbeitnow_raw:
                    arbeit_df = pd.DataFrame(arbeitnow_raw)
            
                    st.markdown("#### 🇪🇺 Arbeitnow Debug Details")
            
                    st.write({
                        "Total Arbeitnow jobs fetched (raw)": len(arbeit_df),
                        "Countries selected": countries,
                        "Unique locations from Arbeitnow": arbeit_df["Location"].dropna().unique()[:10].tolist(),
                        "Work modes": arbeit_df["Work Mode"].value_counts().to_dict()
                    })
            
                    # Show a small preview
                    st.dataframe(
                        arbeit_df[["Title", "Company", "Location", "Work Mode"]].head(5),
                        use_container_width=True
                    )
                else:
                    st.warning("Arbeitnow API returned 0 jobs (raw).")
