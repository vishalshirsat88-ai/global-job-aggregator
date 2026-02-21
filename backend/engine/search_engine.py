import pandas as pd
from concurrent.futures import ThreadPoolExecutor

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

def run_engine(skills, levels, locations, countries, posted_days, include_country_safe=True, deep_search=False):

    raw_locations = locations.copy() if locations else [""]
    locations = [l.strip() for l in raw_locations if l and l.strip()]

    all_rows = []

    search_location = " ".join(raw_locations).strip()

    print("\n==============================")
    print("ENGINE INPUT DEBUG")
    print("Skills:", skills)
    print("Levels:", levels)
    print("Locations:", raw_locations)
    print("Countries:", countries)
    print("Posted Days:", posted_days)
    print("==============================\n")

    # =====================================================
    # 🚀 PARALLEL API FETCHING (MAJOR SPEED BOOST)
    # =====================================================
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
    
    
    if deep_search:
        # JSEARCH tasks
        for skill in skills:
            print(f"\n🚀 JSEARCH CALL")
            print("Query:", skill)
            print("Location:", search_location)
    
            futures.append(
                executor.submit(
                    fetch_jsearch,
                    [skill],
                    levels,
                    countries,
                    posted_days,
                    search_location
                )
            )
    
        # ADZUNA + JOOBLE tasks
        loop_locations = locations if locations else [""]
    
        for loc in loop_locations:
            for skill in skills:
    
                print(f"\n🟡 ADZUNA CALL")
                print("Query:", skill)
                print("Location:", loc)
    
                futures.append(
                    executor.submit(
                        fetch_adzuna,
                        [skill],
                        levels,
                        countries,
                        posted_days,
                        loc
                    )
                )
    
                print(f"\n🔵 JOOBLE CALL")
                print("Query:", skill)
                print("Location:", loc)
    
                futures.append(
                    executor.submit(
                        fetch_jooble,
                        [skill],
                        levels,
                        countries,
                        loc
                    )
                )
    
        # Collect results
        for f in futures:
            try:
                all_rows += f.result()
            except Exception as e:
                print("Fetcher error:", e)


    if not all_rows:
        return pd.DataFrame(), True


    print("\n==============================")
    print("🔎 ENGINE DEBUG — BEFORE SCORING")
    print("Total rows collected:", len(all_rows))
    
    jsearch_count = sum(1 for r in all_rows if r.get("API") == "JSearch")
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

    # Ensure required columns exist (parallel-safe)
    for col in ["Country", "_date", "API"]:
        if col not in df.columns:
            df[col] = None


    print("\n===== DEBUG STAGE 1 — RAW DF =====")
    print("Total rows in DF:", len(df))
    print("JSearch rows in DF:", len(df[df["API"] == "JSearch"]))
    print(df[df["API"] == "JSearch"][["Title","Country"]].head(10))
    print("===================================")

    
    allowed_country_names = {c.upper() for c in countries}
    
    # =============================
    # COUNTRY NORMALIZATION FIX
    # =============================
    COUNTRY_CODE_MAP = {
        "IN": "INDIA",
        "US": "UNITED STATES",
        "GB": "UNITED KINGDOM",
        "CA": "CANADA",
        "AE": "UNITED ARAB EMIRATES",
        "AU": "AUSTRALIA",
        "DE": "GERMANY",
        "FR": "FRANCE",
        "NL": "NETHERLANDS",
        "ES": "SPAIN",
        "IT": "ITALY",
        "PH": "PHILIPPINES"
    }
    
    allowed_country_names = {c.upper() for c in countries}
    
    def normalize_country(val):
        if pd.isna(val):
            return None
        val = str(val).upper().strip()
        return COUNTRY_CODE_MAP.get(val, val)
    
    df["Country"] = df["Country"].apply(normalize_country)

    print("\n===== DEBUG STAGE 2 — AFTER COUNTRY NORMALIZATION =====")
    print("JSearch rows:", len(df[df["API"] == "JSearch"]))
    print(df[df["API"] == "JSearch"][["Title","Country"]].head(10))
    print("=======================================================")

    
    df = df[
        df["Country"].isna() |
        (df["Country"] == "REMOTE") |
        df["Country"].isin(allowed_country_names)
    ]

    print("\n===== DEBUG STAGE 3 — AFTER COUNTRY FILTER =====")
    print("Total rows:", len(df))
    print("JSearch rows:", len(df[df["API"] == "JSearch"]))
    print(df[df["API"] == "JSearch"][["Title","Country"]].head(10))
    print("================================================")

    if df.empty:
        return pd.DataFrame(), True
    
    
    # =====================================================
    # ⭐ STEP 2 — APPLY SCORING AFTER FILTERING
    # =====================================================
    print("\n===== DEBUG STAGE 4 — BEFORE SCORING =====")
    j_df = df[df["API"] == "JSearch"]

    # Ensure _date column exists (parallel fetch safety)
    if "_date" not in df.columns:
        df["_date"] = None
    
    print("JSearch rows entering scoring:", len(j_df))
    print(j_df[["Title","Country","_date"]].head(10))


    
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
    
    jsearch_after = sum(1 for r in ranked_rows if r.get("API") == "JSearch")
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
    is_remote,
    deep_search=False
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
        include_country_safe=True,
        deep_search=deep_search
    )

    return df, fallback
