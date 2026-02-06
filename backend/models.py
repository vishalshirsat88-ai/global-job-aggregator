from pydantic import BaseModel
from typing import List, Optional

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
