import sys
from pathlib import Path
from typing import List, Optional

# Lets this file run from VS Code's "Run" button as well as through uvicorn.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend import database
from backend.recommendation_engine import (
    ENGINE_VERSION,
    get_recommendations,
    generate_dynamic_recommendations,
    list_known_skills,
)

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title="SkillPath AI",
    description="AI Skill Gap and Career Pathway Recommendation System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class FeedbackRequest(BaseModel):
    analysis_id: Optional[int] = None
    relevance: int = Field(..., ge=1, le=5)
    clarity: int = Field(..., ge=1, le=5)
    role: Optional[str] = Field(None, max_length=30)
    comment: Optional[str] = Field(None, max_length=500)


class CandidateRequest(BaseModel):
    target_occupation: str
    current_skills: List[str]
    time_budget_hours: float = Field(..., gt=0, le=1000)


@app.get("/health")
def health():
    return {"status": "healthy", "engine_version": ENGINE_VERSION}


@app.get("/skills")
def skills():
    return list_known_skills()


@app.get("/recommendations")
def recommendations():
    return get_recommendations()


@app.post("/recommend")
def recommend(candidate: CandidateRequest):
    try:
        result = generate_dynamic_recommendations(
            target_occupation=candidate.target_occupation,
            current_skills=candidate.current_skills,
            time_budget_hours=candidate.time_budget_hours,
        )
        try:
            result["analysis_id"] = database.save_analysis(result)
        except Exception:  # the recommendation still works if the database is unavailable
            result["analysis_id"] = None
        return result
    except FileNotFoundError as e:
        raise HTTPException(500, f"Data file missing: {e.filename}. Is the data/ folder next to backend/?")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/history")
def history(limit: int = 10):
    return database.list_history(min(max(limit, 1), 50))


@app.get("/history/{analysis_id}")
def history_item(analysis_id: int):
    result = database.get_analysis(analysis_id)
    if result is None:
        raise HTTPException(404, "Analysis not found")
    return result


@app.post("/feedback")
def feedback(item: FeedbackRequest):
    feedback_id = database.save_feedback(item.analysis_id, item.relevance, item.clarity, item.role, item.comment)
    return {"id": feedback_id, "status": "saved"}


@app.get("/feedback/summary")
def feedback_summary():
    return database.feedback_summary()


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="site")  # keep last: serves style.css, app.js, ...


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
