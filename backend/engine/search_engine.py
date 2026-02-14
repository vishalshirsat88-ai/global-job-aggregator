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

from backend.utils.helpers import filter_and_rank_jobs


# =========================================================
# ENGINE (MULTI-SKILL + MULTI-CITY LOGIC)
# =========================================================
def run_engine(skills, levels, locations, countries, posted_days, include_country_safe=True):

    if not locations:
        locations = [""]

    all_rows = []

    # -----------------------------
    # FETCH FROM ALL SOURCES
    # -----------------------------
    for loc in locations:
        for skill in skills:
            all_rows += fetch_jsearch([skill], levels, countries, posted_days, loc)
            all_rows += fetch_adzuna([skill], levels, countries, posted_days, loc)
            all_rows += fetch_jooble([skill], levels, countries, loc)

    # -----------------------------
    # COUNTRY SAFE SOURCES
    # -----------------------------
    if include_country_safe:
        if "United States" in countries:
            all_rows += fetch_usajobs(skills, posted_days)

        eu_list = {"Germany","France","Netherlands","Ireland","Spain","Italy"}
        if any(c in eu_list for c in countries):
            all_rows += fetch_arbeitnow(skills)

    if not all_rows:
        return pd.DataFrame(), True
    print("\n==============================")
    print("🔎 ENGINE DEBUG — BEFORE SCORING")
    print("Total rows collected:", len(all_rows))
    
    jsearch_count = sum(1 for r in all_rows if r.get("Source") == "JSearch")
    adzuna_count = sum(1 for r in all_rows if r.get("Source") == "Adzuna")
    jooble_count = sum(1 for r in all_rows if r.get("Source") == "Jooble")
    
    print("JSearch rows:", jsearch_count)
    print("Adzuna rows:", adzuna_count)
    print("Jooble rows:", jooble_count)
    print("==============================")



    # =====================================================
    # ⭐ STEP 1 — APPLY COUNTRY FILTER FIRST (CORRECT ORDER)
    # =====================================================
    df = pd.DataFrame(all_rows)
    
    allowed_country_names = {c.upper() for c in countries}
    
    df = df[
        df["Country"].isna() |
        (df["Country"].str.upper() == "REMOTE") |
        df["Country"].str.upper().isin(allowed_country_names)
    ]
    
    if df.empty:
        return pd.DataFrame(), True
    
    
    # =====================================================
    # ⭐ STEP 2 — APPLY SCORING AFTER FILTERING
    # =====================================================
    ranked_rows = filter_and_rank_jobs(
        df.to_dict("records"),   # ✅ FIXED
        skills,
        levels,
        countries,
        top_n=50
    )
    
    print("\n==============================")
    print("🔎 ENGINE DEBUG — AFTER SCORING")
    print("Rows after ranking:", len(ranked_rows))
    
    jsearch_after = sum(1 for r in ranked_rows if r.get("Source") == "JSearch")
    print("JSearch rows after scoring:", jsearch_after)
    print("==============================")
    
    if not ranked_rows:
        return pd.DataFrame(), True
    
    # ✅ IMPORTANT — convert ranked output to df
    df = pd.DataFrame(ranked_rows)

    
    print("\n🔎 FINAL ORDER DEBUG:")
    
    for i, r in enumerate(ranked_rows[:30], 1):
        print(i, r.get("Source"), "-", r.get("Title"))

    return df, False


# =========================================================
# UNIFIED ENTRY POINT
# =========================================================
def run_job_search(
    skills,
    levels,
    locations,
    countries,
    posted_days,
    is_remote
):

    if is_remote:
        rows = []
        rows += fetch_remote_jobs(skills, levels[0] if levels else "", posted_days)
        rows += fetch_arbeitnow(skills)
        rows += fetch_weworkremotely(skills)

        # Apply scoring for remote also
        ranked = filter_and_rank_jobs(rows, skills, levels, countries, top_n=50)

        return ranked, False

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
