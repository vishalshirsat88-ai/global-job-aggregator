from typing import List, Optional
from pydantic import BaseModel, Field


# =========================
# REQUEST SCHEMA
# =========================
class JobSearchRequest(BaseModel):
    skills: List[str] = Field(..., example=["Python", "Data Analyst"])
    levels: List[str] = Field(default_factory=list, example=["Senior"])
    locations: List[str] = Field(default_factory=list, example=["Mumbai"])
    countries: List[str] = Field(default_factory=list, example=["India"])
    posted_days: int = Field(7, ge=1, le=60)
    is_remote: bool = False


# =========================
# SINGLE JOB ROW
# =========================
class JobRow(BaseModel):
    Source: Optional[str]
    Skill: Optional[str]
    Title: Optional[str]
    Company: Optional[str]
    Location: Optional[str]
    Country: Optional[str]
    Work_Mode: Optional[str] = Field(alias="Work Mode")
    Posted: Optional[str]
    Apply: Optional[str]
    _excel: Optional[str]
    _date: Optional[str]


# =========================
# RESPONSE SCHEMA
# =========================
class JobSearchResponse(BaseModel):
    rows: List[dict]
    fallback: bool
