from fastapi import FastAPI
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes

app = FastAPI(
    title="Global Job Aggregator API",
    version="1.0.0"
)

# -------------------------
# Request Schema
# -------------------------
<<<<<<< Updated upstream
=======
from pydantic import BaseModel, Field
from typing import List

class SearchRequest(BaseModel):
    skills: List[str]
    levels: List[str]
    locations: List[str]
    countries: List[str]
    posted_days: int
    is_remote: bool
>>>>>>> Stashed changes

from typing import Optional

class JobRow(BaseModel):
    title: str
    company: Optional[str]
    location: Optional[str]
    url: str
    source: str


class SearchResponse(BaseModel):
    total: int
    returned: int
    page: int
    page_size: int
    rows: List[JobRow]

    # ✅ PAGINATION (ADD THESE)
    page: int = Field(1, ge=1, description="Page number (starts from 1)")
    page_size: int = Field(25, ge=1, le=100, description="Results per page")

# -------------------------
# Health Check
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------
# Job Search Endpoint
# -------------------------
@app.post("/search", response_model=SearchResponse)
<<<<<<< Updated upstream
def search_jobs(req: JobSearchRequest):
=======
def search_jobs(req: SearchRequest):


    # 🔑 cache key must include pagination params
    payload = req.dict()
    cache_key = make_cache_key(payload)

    cached = get_from_cache(cache_key)
    if cached:
        return cached

    # -------------------------
    # Run search engine
    # -------------------------
>>>>>>> Stashed changes
    df_or_rows, fallback = run_job_search(
        skills=req.skills,
        levels=req.levels,
        locations=req.locations,
        countries=req.countries,
        posted_days=req.posted_days,
        is_remote=req.is_remote
    )

<<<<<<< Updated upstream
    # Normalize rows
=======
>>>>>>> Stashed changes
    if req.is_remote:
        rows = df_or_rows
    else:
        rows = df_or_rows.to_dict("records")

    total = len(rows)
    # -------------------------
    # PAGINATION GUARDS
    # -------------------------

    MAX_PAGE_SIZE = 50
    page = max(req.page, 1)
    page_size = min(req.page_size, MAX_PAGE_SIZE)

    
    # -------------------------
    # PAGINATION LOGIC
    # -------------------------
   
    start = (page - 1) * page_size
    end = start + page_size
    paginated_rows = rows[start:end]


<<<<<<< Updated upstream
    return {
        "total": total,
        "returned": len(paginated_rows),
        "page": page,
        "page_size": page_size,
        "rows": paginated_rows
    }
=======
    total = len(jobs)

    # -------------------------
    # PAGINATION (KEEP THIS ✅)
    # -------------------------
    MAX_PAGE_SIZE = 50
    page = max(req.page, 1)
    page_size = min(req.page_size, MAX_PAGE_SIZE)

    start = (page - 1) * page_size
    end = start + page_size

    paginated_jobs = jobs[start:end]

    response = {
        "total": total,
        "returned": len(paginated_jobs),
        "page": page,
        "page_size": page_size,
        "rows": paginated_jobs
    }


    set_cache(cache_key, response)
    return response



>>>>>>> Stashed changes
