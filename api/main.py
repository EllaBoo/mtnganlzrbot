"""
FastAPI backend for Mini App (optional)
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

app = FastAPI(title="Digital Smarty API", version="4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)

# Simple in-memory cache (use Redis in production)
analyses_cache = {}


class QuestionRequest(BaseModel):
    analysis_id: str
    question: str


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "4.0", "name": "Digital Smarty"}


@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    if analysis_id not in analyses_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analyses_cache[analysis_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
