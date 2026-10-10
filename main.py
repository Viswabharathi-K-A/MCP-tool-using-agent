from fastapi import FastAPI
from pydantic import BaseModel
from agent import graph

app = FastAPI()


class ChatRequest(BaseModel):
    query: str
    session_id: str


@app.post("/chat")
async def chat(request: ChatRequest):
    result = graph.invoke({
        "query": request.query,
        "response": ""
    })

    return {
        "response": result["response"]
    }