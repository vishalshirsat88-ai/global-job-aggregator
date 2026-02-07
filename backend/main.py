from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
from backend.payments.paypal import router as paypal_router
app.include_router(paypal_router)

load_dotenv()

from backend.engine.search_engine import run_job_search
from backend.config import validate_env
validate_env()




app = FastAPI(
    title="Global Job Aggregator API",
    version="1.0.0"
)

# -------------------------
# Request Schema
# -------------------------
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

# -------------------------
# Response Schema
# -------------------------
class JobRow(BaseModel):
    title: str
    company: Optional[str]
    location: Optional[str]
    url: str
    source: str
    posted_date: Optional[str]  # ISO string


from typing import Dict, Any
class SearchResponse(BaseModel):
    total: int
    returned: int
    page: int
    page_size: int
    fallback: bool
    rows: List[JobRow]
    debug: Optional[dict] = None

# -------------------------
# Health
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------
# Search
# -------------------------
from fastapi import HTTPException

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
        "_date": raw_date      # 👈 internal only (for sorting)
    }



@app.post("/search", response_model=SearchResponse)
def search_jobs(req: SearchRequest):

    # =========================
    # 🔒 STEP 2 — GUARDRAILS
    # =========================
    if req.page < 1:
        raise HTTPException(
            status_code=400,
            detail="page must be >= 1"
        )

    if req.page_size > 50:
        raise HTTPException(
            status_code=400,
            detail="page_size must be <= 50"
        )

    if not req.skills or len(req.skills) == 0:
        raise HTTPException(
            status_code=400,
            detail="skills must not be empty"
        )

    # -------------------------
    # existing logic continues
    # -------------------------
    
    engine_fallback = False
    # -------------------------
    # Sanitize inputs
    # -------------------------
    skills = clean_list(req.skills)
    levels = clean_list(req.levels)
    locations = clean_list(req.locations)
    countries = clean_list(req.countries)

    did_fallback = False

    # -------------------------
    # REMOTE = HARD OVERRIDE
    # -------------------------
    if req.is_remote:
        locations = []
        countries = []

    # -------------------------
    # COUNTRY REQUIRED (NON-REMOTE)
    # -------------------------
    if not req.is_remote and not countries:
        raise HTTPException(
            status_code=400,
            detail="Country is mandatory unless search is remote."
        )

    # -------------------------
    # FIRST-PASS SEARCH (city-level if provided)
    # -------------------------
    df_or_rows, engine_fallback = run_job_search(
        skills=skills,
        levels=levels,
        locations=locations,
        countries=countries,
        posted_days=req.posted_days,
        is_remote=req.is_remote,
    )

    # -------------------------
    # Normalize rows
    # -------------------------
    raw_jobs = df_or_rows if req.is_remote else df_or_rows.to_dict("records")
    normalized_jobs = [normalize_job_row(j) for j in raw_jobs]


    from collections import Counter
    if req.debug:
        print(Counter(j["source"] for j in normalized_jobs))


    debug_payload = {}

    if req.debug:
        debug_payload["after_deduplication"] = [
            {k: v for k, v in j.items() if k != "_date"}
            for j in normalized_jobs
        ]

    # =========================================================
    # FINAL CITY-LEVEL GUARD + FALLBACK
    # =========================================================
    if not req.is_remote:
        actual_cities = [loc for loc in locations if loc.strip()]

        if actual_cities:
            kept = []
            removed = []

            for job in normalized_jobs:
                if any(
                    city.lower() in (job.get("location") or "").lower()
                    for city in actual_cities
                ):
                    kept.append(job)
                else:
                    removed.append({
                        "job": {k: v for k, v in job.items() if k != "_date"},
                        "reason": "city_filter_mismatch"
                    })

            if kept:
                normalized_jobs = kept
            else:
                did_fallback = True
                df_or_rows, _ = run_job_search(
                    skills=skills,
                    levels=levels,
                    locations=[""],
                    countries=countries,
                    posted_days=req.posted_days,
                    is_remote=False,
                )

                raw_jobs = df_or_rows.to_dict("records") if not df_or_rows.empty else []
                normalized_jobs = [normalize_job_row(j) for j in raw_jobs]

            if req.debug:
                debug_payload["removed_by_city_filter"] = removed


    # -------------------------
    # SORT (LEGACY PARITY)
    # -------------------------
    normalized_jobs = sorted(
        normalized_jobs,
        key=lambda j: j.get("_date") if j.get("_date") is not None else 0,
        reverse=True
    )

    for job in normalized_jobs:
        job.pop("_date", None)

    # -------------------------
    # Pagination
    # -------------------------
    total = len(normalized_jobs)

    page = max(req.page, 1)
    page_size = min(req.page_size, 50)

    start = (page - 1) * page_size
    end = start + page_size
    rows = normalized_jobs[start:end]
    has_more = end < total


    response = {
        "total": total,
        "returned": len(rows),
        "page": page,
        "page_size": page_size,
        "fallback": did_fallback or engine_fallback,
        "rows": rows
    }

    if req.debug:
        response["debug"] = debug_payload

    return response


