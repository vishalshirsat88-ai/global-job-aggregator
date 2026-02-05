BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://localhost:8000"
)

import streamlit as st
import pandas as pd
import requests
import os

from backend.engine.utils import city_match

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
        payload = {
            "skills": skills,
            "levels": levels,
            "locations": locations,
            "countries": countries,
            "posted_days": posted_days,
            "is_remote": is_remote
        }
        
        try:
            resp = requests.post(
                f"{BACKEND_URL}/search",
                json=payload,
                timeout=60
            )
        
            if resp.status_code != 200:
                st.error(f"Backend error: {resp.text}")
                st.stop()
        
            data = resp.json()
            fallback = data.get("fallback", False)
        
            if is_remote:
                df = pd.DataFrame(data["rows"])
            else:
                df = pd.DataFrame(data["rows"])
        
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Cannot reach backend: {e}")
            st.stop()

        
        if is_remote:
            df = pd.DataFrame(df_or_rows)
        else:
            df = df_or_rows
   
        if fallback:
            st.info(
                f"ℹ️ No jobs found for **{location}**. "
                f"Showing country-level jobs instead."
            )

            
        if df.empty:
            st.warning("No jobs found.")
        else:
            # =========================================================
            # 🔒 FINAL CITY-LEVEL GUARD (NON-REMOTE)
            # =========================================================
            if not is_remote:
                # Check if the user actually typed a city/location
                # If 'locations' is empty or just contains an empty string, we SKIP filtering
                actual_cities = [loc for loc in locations if loc.strip()]
                
                if actual_cities:
                    df = df[
                        df["Location"].apply(
                            lambda x: city_match(str(x), actual_cities)
                        )
                    ]

        
                   
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
            
            
