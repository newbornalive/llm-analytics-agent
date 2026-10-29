import os
import secrets
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from .workflow import run_analysis

app = FastAPI(title="LLM Analytics Agent", version="0.1.0")
class AnalyzeRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    mode: Literal["demo", "openai"] = "demo"

@app.get("/health")
def health():
    return {"status": "ok", "default_mode": "demo"}

@app.post("/analyze")
def analyze(request: AnalyzeRequest, authorization: str | None = Header(default=None)):
    if request.mode == "openai":
        token = os.getenv("ANALYTICS_API_TOKEN", "")
        if len(token) < 32:
            raise HTTPException(503, "Configure a local ANALYTICS_API_TOKEN of at least 32 characters to enable paid HTTP requests.")
        if not secrets.compare_digest(authorization or "", "Bearer " + token):
            raise HTTPException(401, "Invalid local token.")
    path = Path(os.getenv("ANALYTICS_DB_PATH", "data/marketing.db"))
    try:
        return run_analysis(request.question, path, request.mode)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
