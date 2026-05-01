from fastapi import APIRouter, HTTPException
from loguru import logger
from api.schemas import QueryRequest, QueryResponse, Citation
from agents.graph import get_graph

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
        return QueryResponse(
            query=request.query,
            answer=result["synthesis"],
            citations=[Citation(**c) for c in result.get("citations", [])],
            intent=result.get("intent", "lookup"),
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
