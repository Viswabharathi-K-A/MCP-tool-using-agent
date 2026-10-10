from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from llm import llm


class AgentState(TypedDict):
    query: str
    response: str


def agent_node(state: AgentState):
    result = llm.invoke(state["query"])

    return {
        "response": result.content
    }


builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)

builder.add_edge(START, "agent")
builder.add_edge("agent", END)

graph = builder.compile()