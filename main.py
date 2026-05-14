import json
import logger_config
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

load_dotenv()

from agent.graph import graph

logger_config = logging.getLogger("main")
app = FastAPI(title="Financial Research Agent")


class QueryRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "online"}


@app.post("/query")
async def query(body: QueryRequest, stream: bool = Query(default=True)):
    logger_config.info("Received query: %r (stream=%s)", body.query, stream)
    messages = {"messages": [HumanMessage(content=body.query)]}

    if stream:
        async def event_stream():
            async for event in graph.astream_events(messages, version="v2"):
                if (
                    event["event"] == "on_chat_model_stream"
                    and event.get("metadata", {}).get("langgraph_node") in ("search_agent", "direct_answer")
                ):
                    chunk = event["data"]["chunk"]
                    content = chunk.content
                    if isinstance(content, list):
                        content = "".join(
                            block.get("text", "") for block in content if isinstance(block, dict)
                        )
                    if content:
                        yield f"data: {json.dumps({'token': content})}\n\n"
            logger_config.info("Streaming query complete")
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    result = await graph.ainvoke(messages)
    answer = result["messages"][-1].content
    logger_config.info("Query complete — answer: %r", answer)
    return {"answer": answer}
