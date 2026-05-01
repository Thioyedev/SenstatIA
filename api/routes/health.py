from fastapi import APIRouter
from api.schemas import HealthResponse
from vectorstore.chroma_store import ChromaStore

router = APIRouter()
_store = None


def _get_store():
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store


@router.get("/health", response_model=HealthResponse)
async def health():
    try:
        store = _get_store()
        count = store.collection.count()
        status = "ok"
    except Exception:
        count = 0
        status = "degraded"
    return HealthResponse(status=status, chunks_indexed=count)
