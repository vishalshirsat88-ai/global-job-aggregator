from typing import List
from pydantic import BaseModel, Field


class JobSearchRequest(BaseModel):
    skills: List[str]
    levels: List[str] = []
    locations: List[str] = []
    countries: List[str] = []
    posted_days: int = Field(7, ge=1, le=60)
    is_remote: bool = False

    # 🔹 pagination inputs
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=5, le=100)


class JobSearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    fallback: bool
    rows: List[dict]
