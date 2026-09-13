from typing import Any

from langgraph.checkpoint.memory import MemorySaver

from app.agent.graph import build_agent_graph
agent_graph: Any | None = None


async def initialize_graph() -> None:
    global agent_graph
    agent_graph = build_agent_graph(MemorySaver())


async def close_graph() -> None:
    global agent_graph
    agent_graph = None
