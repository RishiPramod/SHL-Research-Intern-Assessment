from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

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

    It takes a natural‑language query or a JD URL and returns
    minimum 5, maximum 10 recommended assessments.
    """
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must be a non‑empty string.")

    # Get recommendations (request up to 10, but ensure minimum 5)
    results = recommend_assessments(
        catalogue=CATALOGUE,
        assessment_embeddings=EMBEDDINGS,
        model=MODEL,
        job_description=query,
        top_k=10,
    )

    if results.empty:
        raise HTTPException(status_code=500, detail="No assessments available.")

    # Ensure minimum 5 recommendations (requirement: minimum 5, maximum 10)
    # If balanced selection returned fewer than 5, get top-k by similarity to fill
    if len(results) < 5:
        # Get top recommendations by similarity (without balanced selection)
        query_embedding = MODEL.encode(
            query,
            normalize_embeddings=True,
        ).reshape(1, -1)
        similarities = cosine_similarity(query_embedding, EMBEDDINGS)[0]
        
        # Get top 10 by similarity
        top_indices = similarities.argsort()[-10:][::-1]
        fallback_results = CATALOGUE.iloc[top_indices].copy()
        fallback_results["relevance_score"] = similarities[top_indices]
        fallback_results = fallback_results.reset_index(drop=True)
        
        # Combine with existing results, removing duplicates
        existing_urls = set(results["url"].tolist())
        additional_results = []
        for _, row in fallback_results.iterrows():
            if row["url"] not in existing_urls:
                additional_results.append(row)
                existing_urls.add(row["url"])
                if len(results) + len(additional_results) >= 10:
                    break
        
        # Combine results
        if additional_results:
            additional_df = pd.DataFrame(additional_results)
            results = pd.concat([results, additional_df], ignore_index=True)
        
        # Ensure we have at least 5 (or as many as available if catalogue is small)
        min_results = min(5, len(CATALOGUE))
        if len(results) < min_results:
            # If still not enough, take top by similarity
            top_indices = similarities.argsort()[-min_results:][::-1]
            results = CATALOGUE.iloc[top_indices].copy()
            results["relevance_score"] = similarities[top_indices]
            results = results.reset_index(drop=True)

    # Limit to maximum 10
    results = results.head(10)

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


