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
    print("\n==============================")
    print("SCORING JOB")
    print("API:", job.get("API"))
    print("Title:", job.get("Title"))
    print("Country:", job.get("Country"))
    print("Date:", job.get("_date"))
    print("==============================")


    
    title = str(job.get("Title") or "").lower()
    desc = str(job.get("Description") or "").lower()
    country_val = job.get("Country")

    if not country_val:
        location = ""
    else:
        location = str(country_val).lower()

    source = str(job.get("Source") or "").lower()
    api = str(job.get("API") or "").lower()


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
    if api == "jsearch":
        score += 50   # ← THIS FIXES EVERYTHING
    elif api == "adzuna":
        score += 30
    elif api == "jooble":
        score += 10




    # --- Penalize junk
    if "sponsored" in title or "promoted" in title:
        score -= 40

    print(f"FINAL SCORE → {job.get('Title')} | API={api} | Score={score}")


    if job.get("API") == "JSearch":
        print("FINAL SCORE:", score)
        print("-----------------------------")

    
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
            (job.get("API") or "").lower(),   # ⭐ CRITICAL FIX
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
    
        api = str(job.get("API") or "").lower()
    
        # Jooble stricter threshold
        threshold = 50 if api == "jooble" else 30

        if score >= threshold:   # Quality threshold
            print("✅ KEPT:", job.get("Title"), "Score:", score)
            job["_score"] = score
            scored.append(job)
        else:
            if job.get("API") == "JSearch":
                    print("❌ DROPPED BY THRESHOLD:", job.get("Title"), "Score:", score)

            
    # Step 3 — Sort by score
    scored.sort(key=lambda x: x["_score"], reverse=True)

    # Step 4 — Return top N
    return scored[:top_n]

# =========================================================
# ⭐ NEW — GLOBAL SKILL EXPANSION ENGINE
# =========================================================

SKILL_EXPANSION_MAP = {

    # --- YOUR CUSTOM SKILLS ---
    "developer": ["Full Stack Engineer", "Backend Developer", "Software Architect"],
    "frontend": ["React Developer", "Vue.js Engineer"],
    "backend": ["Node.js Developer", "Java Spring Boot", "Python API Engineer"],

    "tester": ["QA Automation Engineer", "SDET", "Selenium Engineer"],
    "qa": ["Test Architect", "Mobile App Tester"],

    "wfm": ["Workforce Management", "Workforce Planner", "Resource Scheduler", "Intraday Analyst", "Real Time Analyst", "RTA Specialist"],
    "rta": ["Real Time Analyst", "RTA Specialist"],

    "mis": ["MIS Executive", "ERP Specialist"],
    "reporting": ["Power BI Developer", "SQL Reporting Analyst"],

    "banking": ["Investment Banker", "Relationship Manager"],
    "fintech": ["Risk Management Analyst", "Compliance Officer"],

    # --- GLOBAL TECH SKILLS ---
    "python": ["Python Developer", "Django Developer", "Data Scientist"],
    "java": ["Java Developer", "Spring Boot Engineer"],
    "react": ["React Developer", "Frontend Engineer"],
    "node": ["Node.js Developer", "Backend Engineer"],
    "devops": ["DevOps Engineer", "Site Reliability Engineer"],
    "cloud": ["Cloud Engineer", "AWS Engineer", "Azure Engineer"],

    "data": ["Data Analyst", "Data Scientist", "Business Intelligence"],
    "ai": ["AI Engineer", "Machine Learning Engineer"],
}


def expand_skill(skill: str):
    """
    Expands a single skill into multiple related keywords.
    If not found, returns original skill only.
    """

    if not skill:
        return []

    key = skill.lower().strip()

    if key in SKILL_EXPANSION_MAP:
        return [skill] + SKILL_EXPANSION_MAP[key]

    return [skill]


