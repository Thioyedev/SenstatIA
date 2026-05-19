import os

from fastapi import APIRouter

from api.schemas import DocumentInfo
from ingestion.pipeline import load_sources

router = APIRouter()
_store = None


def _get_store():
    global _store
    if _store is None:
        if os.getenv("USE_QDRANT", "false").lower() == "true":
            from vectorstore.qdrant_store import QdrantStore
            _store = QdrantStore()
        else:
            from vectorstore.chroma_store import ChromaStore
            _store = ChromaStore()
    return _store


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents():
    store = _get_store()
    sources = load_sources()
    docs = []
    for source in sources:
        try:
            count = store.count(where={"source_id": source["id"]})
        except Exception:
            count = 0

        docs.append(DocumentInfo(
            source_id=source["id"],
            institution=source.get("institution", ""),
            report_name=source.get("name", ""),
            year=source.get("year"),
            topics=source.get("topics", []),
            url=source.get("url", ""),
            chunk_count=count,
        ))
    return docs
