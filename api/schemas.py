from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class QueryRequest(BaseModel):
    query: str
    messages: list[Message] = []
    n_results: int = 8
    filter_source: str | None = None


class Citation(BaseModel):
    institution: str | None = None
    report_name: str | None = None
    year: int | None = None
    page: int | None = None
    url: str | None = None
    source_id: str | None = None


class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: list[Citation]
    intent: str
    viz: dict | None = None


class DocumentInfo(BaseModel):
    source_id: str
    institution: str
    report_name: str
    year: int
    topics: list[str]
    url: str
    chunk_count: int


class HealthResponse(BaseModel):
    status: str
    chunks_indexed: int
    version: str = "0.1.0"
