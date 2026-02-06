import streamlit as st
import requests
import pandas as pd
import re
from datetime import datetime, timedelta
BACKEND_URL = "https://solid-train-wr695xqwjrrgc9v7j-8000.app.github.dev"


def call_backend_search(payload):
    resp = requests.post(
        f"{BACKEND_URL}/search",
        json=payload,
        timeout=60
    )
    resp.raise_for_status()
    return resp.json()

# =========================================================
# COUNTRY MAP
# =========================================================
COUNTRIES = {
    "India": "in",
    "United States": "us",
    "United Kingdom": "gb",
    "United Arab Emirates": "ae",
    "Canada": "ca",
    "Australia": "au"
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
    return re.search(rf"\b{re.escape(skill.lower())}\b", (text or "").lower())

def work_mode(text):
    t = (text or "").lower()
    if "remote" in t:
        return "Remote"
    if "hybrid" in t:
        return "Hybrid"
    return "On-site"

def city_match(city, text):
    if not city:
        return False
    return re.search(rf"\b{re.escape(city.lower())}\b", (text or "").lower()) is not None

def text_contains(text, items):
    t = (text or "").lower()
    return any(i.lower() in t for i in items)

def excel_link(url):
    return f'=HYPERLINK("{url}","Apply")' if url else ""


# =========================================================
# STREAMLIT UI
# =========================================================
st.set_page_config(page_title="Global Job Aggregator", layout="wide")
st.title("🌍 Global Job Aggregator")

skills = [s.strip() for s in st.text_input("Skills", "WFM").split(",") if s.strip()]
levels = [l.strip() for l in st.text_input("Levels", "Manager").split(",") if l.strip()]
location = st.text_input("Location (city or Remote, comma separated)", "")

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

if st.button("Run Job Search"):
    with st.spinner("Fetching jobs..."):
        payload = {
            "skills": skills,
            "levels": levels,
            "locations": [] if is_remote else [location],
            "countries": [] if is_remote else countries,
            "posted_days": posted_days,
            "is_remote": is_remote,
            "page": 1,
            "page_size": 20
        }

        result = call_backend_search(payload)
        rows = result["rows"]
        if not rows:
            df = pd.DataFrame()

        fallback = result["fallback"]
        df = pd.DataFrame(rows)
        if "url" in df.columns:
            df = df.rename(columns={"url": "Apply"})


    if fallback:
        st.info(
            f"ℹ️ No jobs found for **{location}**. "
            f"Showing country-level jobs instead."
        )


    if df.empty:
        st.warning("No jobs found.")
    else:
        if "posted_date" in df.columns:
            df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce")
            df = df.sort_values(by=["posted_date"], ascending=False)


        st.success(f"✅ Found {len(df)} jobs")
        st.dataframe(
            df,
            use_container_width=True,
            column_config={"Apply": st.column_config.LinkColumn("Apply Now")}
        )

        csv_df = df.copy()


        st.download_button(
            "⬇️ Download CSV",
            csv_df.to_csv(index=False),
            "job_results.csv"
        )

