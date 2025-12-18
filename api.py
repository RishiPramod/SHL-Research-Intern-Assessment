from typing import Dict, List

import numpy as np

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from data.catalogue import load_catalogue
from models.embedding_model import load_embedding_model
from recommender.engine import recommend_assessments

app = FastAPI(title="SHL Assessment Recommendation API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates")


class RecommendRequest(BaseModel):
    query: str


class AssessmentResponse(BaseModel):
    url: str
    name: str
    adaptive_support: str
    description: str
    duration: int
    remote_support: str
    test_type: List[str]


class RecommendResponse(BaseModel):
    recommended_assessments: List[AssessmentResponse]


@app.on_event("startup")
def _load_resources() -> None:
    """
    Load model, catalogue and pre‑compute embeddings once when the
    API server starts.
    """
    print("Loading embedding model...")
    global MODEL, CATALOGUE, EMBEDDINGS
    MODEL = load_embedding_model()
    print("Loading catalogue...")
    CATALOGUE = load_catalogue()
    print("Pre-computing embeddings...")
    EMBEDDINGS = MODEL.encode(
        CATALOGUE["combined_text"].tolist(),
        normalize_embeddings=True,
    )
    print("Startup complete.")


@app.get("/health")
def health() -> Dict[str, str]:
    """
    Simple health‑check endpoint required by the assignment.
    """
    return {"status": "healthy"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """
    Simple web UI for recruiters / hiring managers to use the engine.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/recommend", response_model=RecommendResponse)
def recommend(payload: RecommendRequest) -> RecommendResponse:
    """
    Main recommendation endpoint.

    It takes a natural‑language query or a JD URL and returns up to
    10 recommended assessments.
    """
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must be a non‑empty string.")

    results = recommend_assessments(
        catalogue=CATALOGUE,
        assessment_embeddings=EMBEDDINGS,
        model=MODEL,
        job_description=query,
        top_k=10,
    )

    if results.empty:
        # This should not happen in practice, but keep the contract:
        raise HTTPException(status_code=500, detail="No assessments available.")

    recs: List[AssessmentResponse] = []
    for _, row in results.iterrows():
        recs.append(
            AssessmentResponse(
                url=row.get("url", ""),
                name=row.get("name", ""),
                adaptive_support=row.get("adaptive_support", "No"),
                description=row.get("description", ""),
                duration=int(row.get("duration_minutes", row.get("duration", 0))),
                remote_support=row.get("remote_support", "Yes"),
                test_type=row.get("test_type", []),
            )
        )

    return RecommendResponse(recommended_assessments=recs)


