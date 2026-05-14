import json
import logger_config
import logging
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

load_dotenv()

from agent.graph import graph, stateless_graph

logger_config = logging.getLogger("main")
app = FastAPI(title="Financial Research Agent")


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "online"}


@app.post("/query")
async def query(body: QueryRequest, stream: bool = Query(default=True)):
    logger_config.info("Received query: %r (stream=%s, session=%s)", body.query, stream, body.session_id)

    if body.session_id:
        active_graph = graph
        config = {"configurable": {"thread_id": body.session_id}}
    else:
        active_graph = stateless_graph
        config = {}

    messages = {"messages": [HumanMessage(content=body.query)]}

    if stream:
        async def event_stream():
            if body.session_id:
                yield f"data: {json.dumps({'session_id': body.session_id}, ensure_ascii=False)}\n\n"
            async for event in active_graph.astream_events(messages, config=config, version="v2"):
                node = event.get("metadata", {}).get("langgraph_node")
                if (
                    event["event"] == "on_chat_model_stream"
                    and node in ("search_agent", "direct_answer", "greeting_reply")
                ):
                    chunk = event["data"]["chunk"]
                    content = chunk.content
                    if isinstance(content, list):
                        content = "".join(
                            block.get("text", "") for block in content if isinstance(block, dict)
                        )
                    if content:
                        yield f"data: {json.dumps({'token': content}, ensure_ascii=False)}\n\n"
                elif (
                    event["event"] == "on_chain_end"
                    and node == "off_topic_reply"
                ):
                    output_messages = event["data"].get("output", {}).get("messages", [])
                    if output_messages:
                        content = output_messages[-1].content
                        if content:
                            yield f"data: {json.dumps({'token': content}, ensure_ascii=False)}\n\n"
            logger_config.info("Streaming query complete (session=%s)", body.session_id)
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    result = await active_graph.ainvoke(messages, config=config)
    answer = result["messages"][-1].content
    logger_config.info("Query complete (session=%s) — answer: %r", body.session_id, answer)
    response = {"answer": answer}
    if body.session_id:
        response["session_id"] = body.session_id
    return response
