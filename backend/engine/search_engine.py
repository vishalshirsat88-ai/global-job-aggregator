import pandas as pd
from backend.engine.fetchers import (
    fetch_remote_jobs,
    fetch_weworkremotely,
    fetch_arbeitnow,
    fetch_jsearch,
    fetch_adzuna,
    fetch_jooble,
    fetch_usajobs
)


from backend.utils.helpers import city_match


# =========================================================
# ENGINE (MULTI-SKILL + MULTI-CITY LOGIC)
# =========================================================
def run_engine(skills, levels, locations, countries, posted_days, include_country_safe=False):

    # 🔑 CRITICAL FIX
    if not locations:
        locations = [""]
    all_rows = []

    for loc in locations:
        for skill in skills:
            all_rows += fetch_jsearch([skill], levels, countries, posted_days, loc)
            all_rows += fetch_adzuna([skill], levels, countries, posted_days, loc)
            all_rows += fetch_jooble([skill], levels, countries, loc)
    # ---------------------------------
    # COUNTRY-SAFE SOURCES (ONCE ONLY)
    # ---------------------------------
    if include_country_safe:
        if "United States" in countries:
            all_rows += fetch_usajobs(skills, posted_days)
    
        eu_list = {"Germany","France","Netherlands","Ireland","Spain","Italy"}
        if any(c in eu_list for c in countries):
            all_rows += fetch_arbeitnow(skills)

    if not all_rows:
        return pd.DataFrame(), True

    df = pd.DataFrame(all_rows)

    
    # -----------------------------
    # FIXED COUNTRY FILTER
    # -----------------------------
    allowed_country_names = {c.upper() for c in countries}
    
    df = df[
        df["Country"].isna() | 
        (df["Country"].str.upper() == "REMOTE") |
        df["Country"].str.upper().isin(allowed_country_names)
    ]




    if df.empty:
        return pd.DataFrame(), True

    # Deduplicate across locations
    df = df.drop_duplicates(
        subset=["Title", "Company", "Location", "Source"]
    )

    return df, False

    def run_job_search(
        skills,
        levels,
        locations,
        countries,
        posted_days,
        is_remote
    ):
        """
        Single entry point for job search.
        This mirrors Streamlit behavior exactly.
        """

        # -----------------------
        # REMOTE SEARCH
        # -----------------------
        if is_remote:
            rows = []
            rows += fetch_remote_jobs(
                skills,
                levels[0] if levels else "",
                posted_days
            )
            rows += fetch_arbeitnow(skills)
            rows += fetch_weworkremotely(skills)
            return rows, False

        # -----------------------
        # NON-REMOTE SEARCH
        # -----------------------
        df, fallback = run_engine(
            skills,
            levels,
            locations,
            countries,
            posted_days,
            include_country_safe=True
        )

        # 🔁 COUNTRY-LEVEL FALLBACK (same as Streamlit)
        if fallback:
            df, _ = run_engine(
                skills,
                levels,
                locations=[""],
                countries=countries,
                posted_days=posted_days,
                include_country_safe=True
            )

        return df, fallback
def run_job_search(
    skills,
    levels,
    locations,
    countries,
    posted_days,
    is_remote
):
    """
    Unified entry point for both Streamlit & FastAPI
    """

    if is_remote:
        rows = []
        rows += fetch_remote_jobs(skills, levels[0] if levels else "", posted_days)
        rows += fetch_arbeitnow(skills)
        rows += fetch_weworkremotely(skills)
        return rows, False

    # Non-remote flow
    df, fallback = run_engine(
        skills=skills,
        levels=levels,
        locations=locations,
        countries=countries,
        posted_days=posted_days,
        include_country_safe=True
    )

    return df, fallback

