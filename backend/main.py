from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

from engine.search_engine import run_job_search

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


# -------------------------
# Health Check
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------
# Job Search Endpoint
# -------------------------
@app.post("/search")
def search_jobs(req: SearchRequest):
    df_or_rows, fallback = run_job_search(
        skills=req.skills,
        levels=req.levels,
        locations=req.locations,
        countries=req.countries,
        posted_days=req.posted_days,
        is_remote=req.is_remote
    )

    # Remote returns rows, non-remote returns DataFrame
    if req.is_remote:
        jobs = df_or_rows
    else:
        jobs = df_or_rows.to_dict("records")

    return {
        "total": len(jobs),
        "fallback": fallback,
        "jobs": jobs
    }

