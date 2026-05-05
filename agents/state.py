from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    query: str
    intent: str                       # lookup | trend | compare | compute | viz | mixed
    retrieved_chunks: List[dict]
    trend_output: Optional[dict]
    compare_output: Optional[dict]
    compute_output: Optional[dict]
    viz_output: Optional[dict]
    synthesis: str
    citations: List[dict]
    messages: Annotated[List[BaseMessage], operator.add]
    conversation_history: List[dict]  # [{"role": "user"|"assistant", "content": str}]
