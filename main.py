import logger_config
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
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
async def query(body: QueryRequest):
    logger_config.info("Received query: %r", body.query)
    messages = {"messages": [HumanMessage(content=body.query)]}
    result = await graph.ainvoke(messages)
    answer = result["messages"][-1].content
    logger_config.info("Query complete — answer: %r", answer)
    return {"answer": answer}
