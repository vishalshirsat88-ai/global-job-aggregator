from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
import pandas as pd
from typing import List, Optional
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.engine.fetchers import initialize_active_key

import os
import uuid

# ===============================
# LOAD ENV
# ===============================
load_dotenv()

# ===============================
# PATH SETUP
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# ===============================
# APP INIT
# ===============================
app = FastAPI(
    title="Global Job Aggregator API",
    version="1.0.0"
)

# ===============================
# STATIC + LANDING PAGE
# ===============================
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_landing():
    with open(os.path.join(FRONTEND_DIR, "landing.html"), "r", encoding="utf-8") as f:
        return f.read()

# ===============================
# CORS
# ===============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# DB INIT
# ===============================
from backend.payments.db import init_db, verify_and_register_session
@app.on_event("startup")
def startup_event():
    init_db()

# ===============================
# PAYPAL ROUTER
# ===============================
from backend.payments.paypal import router as paypal_router

app.include_router(
    paypal_router,
    prefix="/payments",
    tags=["Payments"]
)

# ===============================
# RAZORPAY ROUTER  ✅ NEW
# ===============================
from backend.payments.razorpay import router as razorpay_router

app.include_router(
    razorpay_router,
    prefix="/payments",
    tags=["Payments"]
)

# ===============================
# STREAMLIT TOKEN VERIFY API
# ===============================
@app.post("/verify-access")
async def verify_access(request: Request):
    data = await request.json()

    token = data.get("token")
    session_id = data.get("session_id")

    if not token or not session_id:
        return {"success": False, "message": "Missing credentials"}

    valid, message = verify_and_register_session(token, session_id)

    return {
        "success": valid,
        "message": message
    }

# ===============================
# HEALTH CHECK
# ===============================
@app.get("/health")
def health():
    return {"status": "ok"}

# ===============================
# SEARCH ENGINE IMPORTS
# ===============================
from backend.engine.search_engine import run_job_search
from backend.config import validate_env
validate_env()
initialize_active_key()

# ===============================
# REQUEST SCHEMAS
# ===============================
class SearchRequest(BaseModel):
    skills: List[str]
    levels: List[str]
    locations: List[str]
    countries: List[str]
    posted_days: int
    is_remote: bool
    debug: bool = False
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=100)

class JobRow(BaseModel):
    title: str
    company: Optional[str]
    location: Optional[str]
    url: str
    source: str
    posted_date: Optional[str]

class SearchResponse(BaseModel):
    total: int
    returned: int
    page: int
    page_size: int
    fallback: bool
    rows: List[JobRow]
    debug: Optional[dict] = None

# ===============================
# HELPERS
# ===============================
def clean_list(values: list[str]) -> list[str]:
    return [v.strip() for v in values if v and v.strip()]

def normalize_job_row(row: dict) -> dict:
    raw_date = row.get("_date")

    if raw_date:
        try:
            posted_date = raw_date.isoformat()
        except Exception:
            posted_date = str(raw_date)
    else:
        posted_date = None

    return {
        "title": row.get("Title"),
        "company": row.get("Company"),
        "location": row.get("Location"),
        "url": row.get("Apply"),
        "source": row.get("Source"),
        "posted_date": posted_date,
        "_date": raw_date
    }

# ===============================
# SEARCH API
# ===============================
@app.post("/search", response_model=SearchResponse)
def search_jobs(req: SearchRequest):

    if req.page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")

    if req.page_size > 50:
        raise HTTPException(status_code=400, detail="page_size must be <= 50")

    if not req.skills:
        raise HTTPException(status_code=400, detail="skills must not be empty")

    skills = clean_list(req.skills)
    levels = clean_list(req.levels)
    locations = clean_list(req.locations)
    countries = clean_list(req.countries)

    did_fallback = False
    engine_fallback = False

    if req.is_remote:
        locations = []
        countries = []

    if not req.is_remote and not countries:
        raise HTTPException(status_code=400, detail="Country required")

    df_or_rows, engine_fallback = run_job_search(
        skills, levels, locations, countries,
        req.posted_days, req.is_remote
    )

    raw_jobs = df_or_rows if req.is_remote else df_or_rows.to_dict("records")
    normalized_jobs = [normalize_job_row(j) for j in raw_jobs]

    # SORT SAFELY (same behavior as old system)
    df = pd.DataFrame(normalized_jobs)
    
    if not df.empty and "_date" in df.columns:
        df = df.sort_values(
            by="_date",
            ascending=False,
            na_position="last"
        )
    
    normalized_jobs = df.to_dict(orient="records")

    for job in normalized_jobs:
        job.pop("_date", None)

    total = len(normalized_jobs)
    start = (req.page - 1) * req.page_size
    end = start + req.page_size

    rows = normalized_jobs[start:end]

    return {
        "total": total,
        "returned": len(rows),
        "page": req.page,
        "page_size": req.page_size,
        "fallback": did_fallback or engine_fallback,
        "rows": rows
    }
