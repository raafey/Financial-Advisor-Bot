from typing import Annotated, Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict
from agent.prompts import ROUTER_SYSTEM, SEARCH_SYSTEM, DIRECT_SYSTEM

from agent.tools import tools


class State(TypedDict):
    messages: Annotated[list, add_messages]
    route: str


llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)
llm_with_tools = llm.bind_tools(tools)

# ── Nodes

def router(state: State) -> dict:
    """Classify query as needing live search or direct LLM answer."""
    query = state["messages"][-1].content
    response = llm.invoke([
        SystemMessage(content=ROUTER_SYSTEM),
        HumanMessage(content=query),
    ])
    route = "search" if "search" in response.content.strip().lower() else "direct"
    return {"route": route}


def search_agent(state: State) -> dict:
    """LLM with search tools bound — decides what to search and synthesizes results."""
    messages = [SystemMessage(content=SEARCH_SYSTEM)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def direct_answer(state: State) -> dict:
    """LLM answers general financial knowledge questions without search."""
    messages = [SystemMessage(content=DIRECT_SYSTEM)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# ── Conditional edges

def route_after_router(state: State) -> Literal["search_agent", "direct_answer"]:
    return "search_agent" if state["route"] == "search" else "direct_answer"


def route_after_search(state: State) -> Literal["search_tools", "__end__"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "search_tools"
    return END

# ── Graph ─────────────────────────────────────────────────────────────────────

graph = (
    StateGraph(State)
    .add_node("router", router)
    .add_node("search_agent", search_agent)
    .add_node("search_tools", ToolNode(tools))
    .add_node("direct_answer", direct_answer)
    .add_edge(START, "router")
    .add_conditional_edges("router", route_after_router)
    .add_conditional_edges("search_agent", route_after_search)
    .add_edge("search_tools", "search_agent")   # loop back to synthesize
    .add_edge("direct_answer", END)
    .compile()
)
