from fastapi import APIRouter
from api.schemas import DocumentInfo
from ingestion.pipeline import SOURCES
from vectorstore.chroma_store import ChromaStore

router = APIRouter()
_store = None


def _get_store():
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents():
    store = _get_store()
    docs = []
    for source in SOURCES:
        try:
            results = store.collection.get(
                where={"source_id": source["source_id"]},
                include=[],
            )
            count = len(results["ids"])
        except Exception:
            count = 0

        docs.append(DocumentInfo(
            source_id=source["source_id"],
            institution=source["institution"],
            report_name=source["report_name"],
            year=source["year"],
            topics=source["topics"],
            url=source["url"],
            chunk_count=count,
        ))
    return docs
