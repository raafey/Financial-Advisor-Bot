import logging
from typing import Annotated, Literal
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict
from agent.prompts import ROUTER_SYSTEM, SEARCH_SYSTEM, DIRECT_SYSTEM
from agent.tools import tools

logger = logging.getLogger(__name__)

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)
llm_with_tools = llm.bind_tools(tools)


class State(TypedDict):
    messages: Annotated[list, add_messages]
    route: str



# ── Nodes ─────────────────────────────────────────────────────────────────────

def router(state: State) -> dict:
    query = state["messages"][-1].content
    logger.info("Classifying query: %r", query)

    response = llm.invoke([
        SystemMessage(content=ROUTER_SYSTEM),
        HumanMessage(content=query),
    ])
    route = "search" if "search" in response.content.strip().lower() else "direct"
    logger.info("Route decision: %s", route)
    return {"route": route}


def search_agent(state: State) -> dict:
    logger.info("Search agent invoked (message history length: %d)", len(state["messages"]))
    messages = [SystemMessage(content=SEARCH_SYSTEM)] + state["messages"]
    response = llm_with_tools.invoke(messages)

    if hasattr(response, "tool_calls") and response.tool_calls:
        for tc in response.tool_calls:
            logger.info("Tool call requested — tool: %r, input: %r", tc["name"], tc["args"])
    else:
        logger.info("Search agent produced final answer (%d chars)", len(response.content))

    return {"messages": [response]}


def direct_answer(state: State) -> dict:
    logger.info("Answering directly from LLM knowledge (no search needed)")
    messages = [SystemMessage(content=DIRECT_SYSTEM)] + state["messages"]
    response = llm.invoke(messages)
    logger.info("Direct answer produced (%d chars)", len(response.content))
    return {"messages": [response]}

# ── Conditional edges ─────────────────────────────────────────────────────────

def route_after_router(state: State) -> Literal["search_agent", "direct_answer"]:
    return "search_agent" if state["route"] == "search" else "direct_answer"


def route_after_search(state: State) -> Literal["search_tools", "__end__"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        logger.info("Executing search tools, looping back to search agent")
        return "search_tools"
    logger.info("No further tool calls — graph complete")
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
    .add_edge("search_tools", "search_agent")
    .add_edge("direct_answer", END)
    .compile()
)
