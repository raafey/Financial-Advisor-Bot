from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

load_dotenv()

from agent.graph import graph

app = FastAPI(title="Financial Research Agent")


class QueryRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "online"}


@app.post("/query")
async def query(body: QueryRequest):
    messages = {"messages": [HumanMessage(content=body.query)]}
    result = await graph.ainvoke(messages)
    answer = result["messages"][-1].content
    return {"answer": answer}
