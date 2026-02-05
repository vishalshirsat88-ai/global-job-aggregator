from fastapi import FastAPI

from backend.schemas import JobSearchRequest, JobSearchResponse
from engine.search_engine import run_job_search

app = FastAPI(
    title="Global Job Aggregator API",
    version="1.0.0"
)

# -------------------------
# Request Schema
# -------------------------


# -------------------------
# Health Check
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------
# Job Search Endpoint
# -------------------------
@app.post("/search", response_model=JobSearchResponse)
def search_jobs(req: JobSearchRequest):
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
        "rows": jobs
    }


