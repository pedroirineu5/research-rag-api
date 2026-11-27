from typing import Annotated

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

from app.accounts.router import router as accounts_router
from app.chat.router import router as chat_router
from app.chat.router import systems_router

app = FastAPI(title="Research RAG API")
app.include_router(accounts_router)
app.include_router(chat_router)
app.include_router(systems_router)


@app.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok"}
