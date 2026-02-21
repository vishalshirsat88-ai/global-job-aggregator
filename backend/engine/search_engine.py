import re
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

    # ⭐ FIX — Normalize multi-city input
    normalized_locations = []
    for loc in raw_locations:
        if loc and "," in loc:
            normalized_locations.extend([l.strip() for l in loc.split(",") if l.strip()])
        elif loc:
            normalized_locations.append(loc.strip())
    
    locations = normalized_locations
    # ⭐ FIX — Normalize skills (remove duplicates / bad joins)
    normalized_skills = []
    for s in skills:
        if s:
            parts = [p.strip() for p in str(s).split(",") if p.strip()]
            normalized_skills.extend(parts)
    
    skills = list(dict.fromkeys(normalized_skills))  # remove duplicates

    levels = [l.strip() for l in levels if l and l.strip()]
    levels = list(dict.fromkeys(levels))
    

    all_rows = []
 
    print("\n==============================")
    print("ENGINE INPUT DEBUG")
    print("Skills:", skills)
    print("Levels:", levels)
    print("Locations:", locations)
    print("Countries:", countries)
    print("Posted Days:", posted_days)
    print("==============================\n")

    # =====================================================
    # 🚀 PARALLEL API FETCHING (MAJOR SPEED BOOST)
    # =====================================================
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
    
        # =========================
        # JSEARCH (ONLY IF DEEP SEARCH)
        # =========================
        if deep_search:
            for country in (countries if countries else [""]):
                for loc in (locations if locations else [""]):
                    for skill in skills:
                        futures.append(
                            executor.submit(
                                fetch_jsearch,
                                [skill],
                                levels,
                                [country],   # ← FIX HERE
                                posted_days,
                                loc
                            )
                        )


        # =========================
        # 🇺🇸 USAJOBS (ONLY IF USA SELECTED)
        # =========================
        if any(c.upper() in ["USA", "UNITED STATES"] for c in countries):
            for skill in skills:
                print(f"\n🇺🇸 USAJOBS CALL")
                print("Query:", skill)

                futures.append(
                    executor.submit(
                        fetch_usajobs,
                        skill,
                        posted_days
                    )
                )

        # =========================
        # 🇪🇺 ARBEITNOW (EUROPE JOBS)
        # =========================
        EUROPE_COUNTRIES = {
            "GERMANY", "FRANCE", "NETHERLANDS", "SPAIN",
            "ITALY", "BELGIUM", "SWEDEN", "NORWAY",
            "DENMARK", "FINLAND", "POLAND", "PORTUGAL",
            "IRELAND", "AUSTRIA", "SWITZERLAND"
        }

        if any(c.upper() in EUROPE_COUNTRIES for c in countries):
            for skill in skills:
                print(f"\n🇪🇺 ARBEITNOW CALL")
                print("Query:", skill)

                futures.append(
                    executor.submit(
                        fetch_arbeitnow,
                        [skill]
                    )
                )
        
        # =========================
        # ADZUNA + JOOBLE (ALWAYS RUN)
        # =========================
        loop_locations = locations if locations else [""]
    
        for country in (countries if countries else [""]):
            for loc in loop_locations:
                for skill in skills:
        
                    futures.append(
                        executor.submit(
                            fetch_adzuna,
                            [skill],
                            levels,
                            [country],   # ← pass single country
                            posted_days,
                            loc
                        )
                    )
        
                    futures.append(
                        executor.submit(
                            fetch_jooble,
                            [skill],
                            levels,
                            [country],   # ← pass single country
                            loc
                        )
                    )
    
                    
        # Collect results
        for f in futures:
            try:
                all_rows += f.result()
            except Exception as e:
                print("Fetcher error:", e)


    # =====================================================
    # ⭐ FETCH-STAGE COUNTRY FALLBACK (OLD LOGIC RESTORED)
    # =====================================================
    
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
    usajobs_count = sum(1 for r in all_rows if r.get("API") == "USAJobs")
    print("USAJobs rows:", usajobs_count)
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

    
    # Detect if city search was used
    city_search = any(loc.strip() for loc in raw_locations)
    
    if city_search:
        # For city search → allow only rows that contain city in Location
        pattern = "|".join(re.escape(loc.lower()) for loc in locations)

        df = df[
            df["Location"]
            .fillna("")
            .str.lower()
            .str.contains(pattern)
        ]
        
    else:
        # Country-only search → keep previous behavior
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
        # Trigger fallback ONLY if this was a city search
        if raw_locations and any(loc.strip() for loc in raw_locations):
            print("\n🔁 FILTER FALLBACK TRIGGERED → No city matches, retrying with country search\n")
    
            return run_engine(
                skills=skills,
                levels=levels,
                locations=[""],   # remove city constraint
                countries=countries,
                posted_days=posted_days,
                include_country_safe=include_country_safe,
                deep_search=deep_search
            )
    
        # If already country search → truly no results
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
        df.to_dict("records"),
        skills,
        levels,
        countries,
        locations,
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
        ranked = filter_and_rank_jobs(rows, skills, levels, countries, [], top_n=50)

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
