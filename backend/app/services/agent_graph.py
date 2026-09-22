"""将手写循环等价表达为 State / Node / Conditional Edge，复用同一执行器。"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class AgentState(TypedDict):
    messages: list[dict]
    steps: list[dict]
    iterations: int
    calls: list[dict]
    answer: str


async def run_graph(initial: AgentState, decide, execute, max_iterations: int):
    builder = StateGraph(AgentState)
    builder.add_node("agent", decide)
    builder.add_node("tools", execute)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        lambda s: "tools" if s["calls"] else "end",
        {"tools": "tools", "end": END},
    )
    builder.add_edge("tools", "agent")
    graph = builder.compile()
    return await graph.ainvoke(
        initial, config={"recursion_limit": max_iterations * 2 + 4}
    )
