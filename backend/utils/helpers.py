from datetime import datetime

# =========================
# DATE HELPERS (UNCHANGED)
# =========================

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


# =========================
# BASIC HELPERS (UNCHANGED)
# =========================

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
# ⭐ NEW — JOB SCORING ENGINE
# =========================================================

def calculate_job_score(job, skills, levels, countries):
    score = 0

    title = str(job.get("Title") or "").lower()
    desc = str(job.get("Description") or "").lower()
    country_val = job.get("Country")
    location = str(job.get("Country") or "").lower()
    source = str(job.get("Source") or "").lower()

    # --- Skill match in title (MOST IMPORTANT)
    for skill in skills:
        if skill.lower() in title:
            score += 50

    # --- Skill match in description
    for skill in skills:
        if skill.lower() in desc:
            score += 30

    # --- Level match
    for level in levels:
        if level.lower() in title:
            score += 15

    # --- Country match
    for c in countries:
        if c.lower() in location:
            score += 25

    # --- Freshness boost
    if job.get("_date"):
        score += 10

    # --- Source priority boost (FIXED)
    if "jsearch" in source:
        score += 50   # strong boost
    elif "adzuna" in source:
        score += 30
    elif "usajobs" in source:
        score += 20



    # --- Penalize junk
    if "sponsored" in title or "promoted" in title:
        score -= 40

    return score


# =========================================================
# ⭐ NEW — DEDUPLICATION ENGINE
# =========================================================

def deduplicate_jobs(rows):
    seen = set()
    unique = []

    for job in rows:
        key = (
            (job.get("Title") or "").lower(),
            (job.get("Company") or "").lower(),
        )

        if key not in seen:
            seen.add(key)
            unique.append(job)

    return unique


# =========================================================
# ⭐ NEW — FINAL FILTER + RANK ENGINE
# =========================================================

def filter_and_rank_jobs(rows, skills, levels, countries, top_n=50):
    """
    This is the FINAL step before returning jobs to UI.
    """

    # Step 1 — Deduplicate
    rows = deduplicate_jobs(rows)

    scored = []

    # Step 2 — Score each job
    for job in rows:
        score = calculate_job_score(job, skills, levels, countries)

        if score >= 40:   # Quality threshold
            job["_score"] = score
            scored.append(job)

    # Step 3 — Sort by score
    scored.sort(key=lambda x: x["_score"], reverse=True)

    # Step 4 — Return top N
    jsearch_jobs = [j for j in scored if "jsearch" in str(j.get("Source")).lower()]
    other_jobs = [j for j in scored if "jsearch" not in str(j.get("Source")).lower()]

    
    min_jsearch = 5
    selected = jsearch_jobs[:min_jsearch] + other_jobs
    
    return selected[:top_n]

