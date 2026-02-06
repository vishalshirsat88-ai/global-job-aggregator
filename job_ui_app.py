import streamlit as st
import requests
import pandas as pd
import re
from datetime import datetime, timedelta

# Keep your specific backend URL
BACKEND_URL = "https://solid-train-wr695xqwjrrgc9v7j-8000.app.github.dev"

st.set_page_config(page_title="Global Job Aggregator", layout="wide")

# ---------- RESTORED FRONT-END VISUALS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@600;700;800&display=swap');

.stApp {
    background: linear-gradient(135deg, #f5f3ff 0%, #fdf2f8 50%, #fff7ed 100%);
    font-family: 'Inter', sans-serif;
}

/* SIDEBAR STYLING */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #6A5AE0, #B983FF);
    color: white;
}
section[data-testid="stSidebar"] * {
    color: white !important;
}

/* HERO SECTION STYLING */
.hero-title {
    font-family: 'Inter', sans-serif;
    font-size: 52px;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -1px;
    background: linear-gradient(90deg, #4F6CF7 0%, #7A6FF0 50%, #E8A06A 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 18px;
    color: #475569;
    margin-top: 14px;
}

/* BUTTONS */
.stButton>button {
    background: linear-gradient(135deg, #FF5EDF, #FF8A00);
    color: white;
    border-radius: 14px;
    padding: 10px 20px;
    font-weight: 600;
    border: none;
    box-shadow: 0 8px 20px rgba(255, 94, 223, 0.35);
}

/* JOB CARDS */
.job-card {
    background: rgba(255,255,255,0.92);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.08);
    margin-bottom: 22px;
}
.job-title { font-size: 18px; font-weight: 700; color: #1F2937; margin-bottom: 4px; }
.job-company { font-size: 14px; color: #6B7280; margin-bottom: 6px; }
.job-location { font-size: 13px; color: #374151; margin-bottom: 10px; }

.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}
.badge-remote { background: linear-gradient(135deg, #6A5AE0, #B983FF); color: white; }
.badge-hybrid { background: linear-gradient(135deg, #00C9A7, #92FE9D); color: #064E3B; }
.badge-onsite { background: #E5E7EB; color: #374151; }

.apply-btn {
    background: linear-gradient(135deg, #FF5EDF, #FF8A00);
    color: white !important;
    padding: 8px 16px;
    border-radius: 12px;
    font-weight: 600;
    text-decoration: none;
}

/* DOWNLOAD BUTTON */
.download-btn button {
    background: linear-gradient(135deg, #00C9A7, #92FE9D) !important;
    color: #064E3B !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- HERO SECTION ----------
st.markdown("""
<div style="padding: 60px 0 40px 0; text-align:center;">
    <div class="hero-title">Global Job Aggregator</div>
    <div class="hero-subtitle">Search smarter. Apply faster.</div>
</div>
""", unsafe_allow_html=True)

# ---------- INPUT AREA ----------
skills = [s.strip() for s in st.text_input("Skills", "WFM").split(",") if s.strip()]
levels = [l.strip() for l in st.text_input("Levels", "Manager").split(",") if l.strip()]
location_input = st.text_input("Location (city or Remote)", "")

is_remote = location_input.strip().lower() == "remote"
countries = st.multiselect(
    "Country", 
    options=["India", "United States", "United Kingdom", "United Arab Emirates", "Canada", "Australia"], 
    default=["India"], 
    disabled=is_remote
)

if not is_remote and not countries:
    st.error("Country is mandatory unless location is Remote.")
    st.stop()

posted_days = st.slider("Posted within last X days", 1, 60, 7)

# ---------- ACTION BAR ----------
col_run, col_toggle, col_dl = st.columns([2, 3, 2])
with col_run:
    run_btn = st.button("🚀 Run Job Search")
with col_toggle:
    view_mode = st.toggle("Classic view", value=False) # Default to Card View for better visuals
with col_dl:
    dl_placeholder = st.empty()

# ---------- BACKEND LOGIC ----------
def call_backend_search(payload):
    resp = requests.post(f"{BACKEND_URL}/search", json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()

if run_btn:
    with st.spinner("Fetching jobs..."):
        payload = {
            "skills": skills,
            "levels": levels,
            "locations": [] if is_remote else [location_input],
            "countries": countries,
            "posted_days": posted_days,
            "is_remote": is_remote,
            "page": 1,
            "page_size": 20
        }
        
        try:
            result = call_backend_search(payload)
            rows = result.get("rows", [])
            df = pd.DataFrame(rows)
            fallback = result.get("fallback", False)
        except Exception as e:
            st.error(f"Backend Error: {e}")
            df = pd.DataFrame()

    if df.empty:
        st.warning("No jobs found.")
    else:
        # Standardize Columns
        if "url" in df.columns: df = df.rename(columns={"url": "Apply"})
        if "skill" not in df.columns: df["skill"] = ", ".join(skills)
        if "posted_date" in df.columns:
            df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce")
            df = df.sort_values(by="posted_date", ascending=False)

        st.success(f"✅ Found {len(df)} jobs")

        if view_mode:
            # ---------- CLASSIC TABLE VIEW ----------
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "Apply": st.column_config.LinkColumn(
                        "Apply Now",
                        display_text="Apply Now"
                    )
                }
            )
        else:
            # ---------- CARD VIEW (FIXED & CLEANED) ----------
            cols = st.columns(2)
            for i, row in df.iterrows():
                # Logic to handle missing values safely
                title = row.get('title') or row.get('Title') or "Job Title"
                company = row.get('company') or row.get('Company') or "Company"
                loc = row.get('location') or row.get('Location') or "Not Specified"
                link = row.get('Apply') or row.get('apply_link') or "#"
                mode = str(row.get("work_mode") or "On-site")
                
                # Determine Badge Color
                if "remote" in mode.lower():
                    b_class = "badge-remote"
                elif "hybrid" in mode.lower():
                    b_class = "badge-hybrid"
                else:
                    b_class = "badge-onsite"

                with cols[i % 2]:
                    card_html = f"""
                    <div class="job-card">
                        <div class="job-title">{title}</div>
                        <div class="job-company">{company}</div>
                        <div class="job-location">📍 {loc}</div>
                        <div style="margin-top: 8px;">
                            <span class="badge {b_class}">{mode}</span>
                        </div>
                        <div class="job-actions" style="display: flex; justify-content: flex-end; margin-top: 10px;">
                            <a class="apply-btn" href="{link}" target="_blank">Apply →</a>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

        # DOWNLOAD BUTTON
        with col_dl:
            st.markdown('<div class="download-btn">', unsafe_allow_html=True)
            dl_placeholder.download_button("⬇️ Download CSV", df.to_csv(index=False), "job_results.csv")
            st.markdown('</div>', unsafe_allow_html=True)