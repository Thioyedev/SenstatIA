import re
from fastapi import APIRouter, HTTPException
from loguru import logger
from api.schemas import QueryRequest, QueryResponse, Citation
from agents.graph import get_graph

_INLINE_CITE_RE = re.compile(r'\s*\[[^\]]*p\.\s*\d+\]')

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        graph = get_graph()
        result = graph.invoke({
            "query": request.query,
            "intent": "",
            "retrieved_chunks": [],
            "trend_output": None,
            "compare_output": None,
            "compute_output": None,
            "viz_output": None,
            "synthesis": "",
            "citations": [],
            "messages": [],
        })
        answer = _INLINE_CITE_RE.sub("", result["synthesis"]).strip()
        return QueryResponse(
            query=request.query,
            answer=answer,
            citations=[Citation(**c) for c in result.get("citations", [])],
            intent=result.get("intent", "lookup"),
            viz=result.get("viz_output"),
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
