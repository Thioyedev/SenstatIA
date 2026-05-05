from pydantic import BaseModel
from typing import Optional, List


class QueryRequest(BaseModel):
    query: str
    n_results: int = 8
    filter_source: Optional[str] = None


class Citation(BaseModel):
    institution: Optional[str] = None
    report_name: Optional[str] = None
    year: Optional[int] = None
    page: Optional[int] = None
    url: Optional[str] = None
    source_id: Optional[str] = None


class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[Citation]
    intent: str
    viz: Optional[dict] = None


class DocumentInfo(BaseModel):
    source_id: str
    institution: str
    report_name: str
    year: int
    topics: List[str]
    url: str
    chunk_count: int


class HealthResponse(BaseModel):
    status: str
    chunks_indexed: int
    version: str = "0.1.0"
