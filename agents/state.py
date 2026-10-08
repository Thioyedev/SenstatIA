import operator
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    query: str
    intent: str  # lookup | trend | compare | compute | viz | mixed
    retrieved_chunks: list[dict]
    trend_output: dict | None
    compare_output: dict | None
    compute_output: dict | None
    viz_output: dict | None
    synthesis: str
    citations: list[dict]
    messages: Annotated[list[BaseMessage], operator.add]
    conversation_history: list[dict]  # [{"role": "user"|"assistant", "content": str}]
