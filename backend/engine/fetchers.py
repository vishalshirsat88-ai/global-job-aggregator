import os
import requests
import feedparser
from datetime import datetime, timedelta

# =========================
# ENV VARIABLES
# =========================
RAPIDAPI_KEYS = os.getenv("RAPIDAPI_KEYS", "").split(",")
JOOBLE_KEY = os.getenv("JOOBLE_KEY")
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")
USAJOBS_EMAIL = os.getenv("USAJOBS_EMAIL")
USAJOBS_API_KEY = os.getenv("USAJOBS_API_KEY")

CURRENT_KEY_INDEX = 0
REMOTIVE_API = "https://remotive.com/api/remote-jobs"

from backend.utils.helpers import (
    normalize_date,
    parse_date,
    skill_match,
    work_mode,
    excel_link
)

# =========================================================
# 🔑 RAPIDAPI KEY ROTATION
# =========================================================
def get_rapidapi_key():
    global CURRENT_KEY_INDEX
    if not RAPIDAPI_KEYS:
        return None
    return RAPIDAPI_KEYS[CURRENT_KEY_INDEX % len(RAPIDAPI_KEYS)].strip()

def rotate_key():
    global CURRENT_KEY_INDEX
    CURRENT_KEY_INDEX += 1


# =========================================================
# 🧠 SMART QUERY EXPANSION
# =========================================================
def expand_skill(skill):
    skill = skill.lower().strip()

    if skill in SKILL_EXPANSION_MAP:
        return [skill] + SKILL_EXPANSION_MAP[skill]

    # If not found → use original skill
    return [skill]


    # =========================================================
    # 🌍 GLOBAL SKILL EXPANSION MAP (PRODUCTION READY)
    # =========================================================
    
    SKILL_EXPANSION_MAP = {
    
        # --- YOUR CUSTOM SKILLS ---
        "developer": ["Full Stack Engineer", "Backend Developer", "Software Architect", "Systems Programmer"],
        "frontend": ["React Developer", "Vue.js Engineer", "Frontend Architect", "Tailwind CSS Specialist"],
        "backend": ["Node.js Developer", "Go Developer", "Java Spring Boot", "Python API Engineer"],
    
        "tester": ["QA Automation Engineer", "SDET", "Selenium Engineer", "Performance Tester"],
        "manual testing": ["Quality Assurance Analyst", "UAT Coordinator", "Regression Tester"],
        "qa": ["SDET Manager", "Test Architect", "Mobile App Tester", "Security QA"],
    
        "wfm": ["Workforce Planner", "Resource Scheduler", "Intraday Analyst", "Capacity Planning Manager"],
        "workforce": ["Real Time Management Specialist", "WFM Strategist", "Forecasting Analyst"],
    
        "mis": ["MIS Executive", "Data Operations Manager", "Information Systems Manager", "ERP Specialist"],
        "reporting": ["SQL Reporting Analyst", "Power BI Developer", "Automation Specialist", "VBA Expert"],
    
        "banking": ["Investment Banker", "Retail Banking Manager", "Relationship Manager", "Corporate Finance"],
        "fintech": ["Payments Architect", "Compliance Officer", "Risk Management Analyst", "KYC Specialist"],
        "investment": ["Portfolio Manager", "Equity Research Analyst", "Asset Management", "Quant Analyst"],
        "compliance": ["AML Analyst", "Financial Crime Investigator", "Regulatory Affairs Manager"],
    
    
        # --- TOP GLOBAL TECH SKILLS ---
        "python": ["Python Developer", "Django Developer", "FastAPI Engineer", "Data Scientist"],
        "java": ["Java Developer", "Spring Boot Engineer", "Backend Java Developer"],
        "javascript": ["JS Developer", "Frontend Developer", "Full Stack JavaScript"],
        "react": ["React Developer", "Frontend React Engineer"],
        "node": ["Node.js Developer", "Backend Node Engineer"],
        "angular": ["Angular Developer", "Frontend Angular Engineer"],
    
        "devops": ["DevOps Engineer", "Cloud DevOps", "Site Reliability Engineer"],
        "cloud": ["Cloud Engineer", "AWS Specialist", "Azure Engineer", "GCP Engineer"],
    
        "aws": ["AWS Engineer", "Cloud Architect", "DevOps AWS"],
        "azure": ["Azure Engineer", "Cloud Azure Architect"],
        "gcp": ["Google Cloud Engineer", "GCP Architect"],
    
        "docker": ["Container Engineer", "Docker Specialist"],
        "kubernetes": ["K8s Engineer", "Cloud Native Engineer"],
    
        "sql": ["Database Developer", "SQL Analyst", "Data Engineer"],
        "data": ["Data Analyst", "Data Scientist", "Business Intelligence"],
        "machine learning": ["ML Engineer", "AI Engineer", "Deep Learning Engineer"],
        "ai": ["Artificial Intelligence Engineer", "LLM Engineer", "AI Researcher"],
    
        "cybersecurity": ["Security Engineer", "SOC Analyst", "Penetration Tester"],
        "blockchain": ["Blockchain Developer", "Smart Contract Engineer", "Web3 Developer"],
    
    
        # --- BUSINESS & MANAGEMENT SKILLS ---
        "project management": ["Project Manager", "Scrum Master", "Agile Coach"],
        "product": ["Product Manager", "Product Owner", "Growth Product Manager"],
        "marketing": ["Digital Marketing Manager", "SEO Specialist", "Performance Marketer"],
        "sales": ["Sales Manager", "Business Development Executive", "Account Manager"],
    
        "hr": ["HR Manager", "Talent Acquisition Specialist", "HR Business Partner"],
        "operations": ["Operations Manager", "Process Improvement Specialist"],
    
        "finance": ["Financial Analyst", "FP&A Manager", "Corporate Finance"],
        "accounting": ["Accountant", "Audit Specialist", "Tax Consultant"],
    
        "supply chain": ["Logistics Manager", "Procurement Specialist", "Inventory Analyst"]
    }


    return expansions.get(skill, [skill])


# =========================================================
# 🎯 RELEVANCE SCORING FILTER
# =========================================================
def relevance_score(job_title, location, skill, user_location):
    score = 0

    title = (job_title or "").lower()
    loc = (location or "").lower()
    skill = skill.lower()

    if skill in title:
        score += 50

    if user_location and user_location.lower() in loc:
        score += 20

    if "senior" in title or "lead" in title:
        score += 10

    return score


# =========================================================
# 🛡️ SAFE REQUEST WITH KEY ROTATION
# =========================================================
def safe_json_request(method, url, **kwargs):
    max_attempts = len(RAPIDAPI_KEYS) if RAPIDAPI_KEYS else 1

    for _ in range(max_attempts):
        try:
            headers = kwargs.get("headers", {})

            if "rapidapi" in url:
                headers["x-rapidapi-key"] = get_rapidapi_key()
                headers["x-rapidapi-host"] = "jsearch.p.rapidapi.com"
                kwargs["headers"] = headers

            r = requests.request(method, url, timeout=20, **kwargs)

            if r.status_code == 429:
                rotate_key()
                continue

            if r.status_code != 200:
                return {}

            return r.json()

        except:
            rotate_key()

    return {}


# =========================================================
# REMOTE SEARCH
# =========================================================
def fetch_remote_jobs(skills, level, posted_days):
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=posted_days)

    for skill in skills:
        queries = expand_skill(skill)

        for q in queries:
            data = safe_json_request(
                "GET",
                "https://jsearch.p.rapidapi.com/search",
                params={"query": f"{q} remote", "num_pages": 1}
            )

            for j in data.get("data", []):
                dt = parse_date(j.get("job_posted_at_datetime_utc",""))
                if dt and dt < cutoff:
                    continue

                rows.append({
                    "Source": j.get("job_publisher"),
                    "Skill": skill,
                    "Title": j.get("job_title"),
                    "Company": j.get("employer_name"),
                    "Location": "Remote",
                    "Country": "Remote",
                    "Work Mode": "Remote",
                    "Posted": j.get("job_posted_at_datetime_utc"),
                    "Apply": j.get("job_apply_link"),
                    "_excel": excel_link(j.get("job_apply_link")),
                    "_date": dt
                })

    return rows


# =========================================================
# JOOBLE FETCHER WITH SMART FILTER
# =========================================================
def fetch_jooble(skills, levels, countries, location):
    rows = []

    for skill in skills:
        data = safe_json_request(
            "POST",
            f"https://jooble.org/api/{JOOBLE_KEY}",
            json={
                "keywords": skill,
                "location": location
            }
        )

        for j in data.get("jobs", []):
            score = relevance_score(
                j.get("title"),
                j.get("location"),
                skill,
                location
            )

            if score < 40:
                continue

            rows.append({
                "Source": "Jooble",
                "Skill": skill,
                "Title": j.get("title"),
                "Company": j.get("company"),
                "Location": j.get("location"),
                "Country": None,
                "Work Mode": work_mode(j.get("title")),
                "Posted": "",
                "Apply": j.get("link"),
                "_excel": excel_link(j.get("link")),
                "_date": None
            })

    return rows
