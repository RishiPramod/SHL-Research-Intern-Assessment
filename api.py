"""
SHL Assessment Recommendation API.

This module provides a FastAPI-based REST API for recommending SHL Individual Test Solutions
assessments based on job descriptions or natural language queries.
"""
import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import config
from data.catalogue import load_catalogue
from models.embedding_model import load_embedding_model
from recommender.engine import recommend_assessments

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    description="REST API for recommending SHL Individual Test Solutions assessments"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))

# Global variables (initialized at startup)
MODEL: Optional[SentenceTransformer] = None
CATALOGUE: Optional[pd.DataFrame] = None
EMBEDDINGS: Optional[np.ndarray] = None


class RecommendRequest(BaseModel):
    """Request model for the /recommend endpoint."""
    query: str = Field(..., description="Job description text or URL", min_length=1)


class AssessmentResponse(BaseModel):
    """Response model for a single recommended assessment."""
    url: str = Field(..., description="Assessment URL from SHL catalogue")
    name: str = Field(..., description="Assessment name")
    adaptive_support: str = Field(..., description="Whether adaptive/IRT is supported")
    description: str = Field(default="", description="Assessment description")
    duration: int = Field(..., description="Assessment duration in minutes", ge=0)
    remote_support: str = Field(..., description="Whether remote testing is supported")
    test_type: List[str] = Field(..., description="List of test type categories")


class RecommendResponse(BaseModel):
    """Response model for the /recommend endpoint."""
    recommended_assessments: List[AssessmentResponse] = Field(
        ...,
        description=f"List of recommended assessments (min {config.MIN_RECOMMENDATIONS}, max {config.MAX_RECOMMENDATIONS})"
    )


@app.on_event("startup")
def _load_resources() -> None:
    """
    Load model, catalogue and pre-compute embeddings once when the API server starts.
    
    This function is called automatically by FastAPI on application startup.
    It initializes:
    - The sentence transformer embedding model
    - The assessment catalogue from CSV
    - Pre-computed embeddings for all assessments (for fast similarity search)
    
    Raises:
        RuntimeError: If catalogue loading or embedding computation fails
    """
    global MODEL, CATALOGUE, EMBEDDINGS
    
    try:
        logger.info("Loading embedding model...")
        MODEL = load_embedding_model()
        logger.info(f"Model loaded: {config.EMBEDDING_MODEL_NAME}")
        
        logger.info("Loading catalogue...")
        CATALOGUE = load_catalogue()
        logger.info(f"Catalogue loaded: {len(CATALOGUE)} assessments")
        
        if len(CATALOGUE) < config.MIN_CATALOGUE_SIZE:
            logger.warning(
                f"Catalogue has only {len(CATALOGUE)} assessments "
                f"(expected at least {config.MIN_CATALOGUE_SIZE})"
            )
        
        logger.info("Pre-computing embeddings...")
        EMBEDDINGS = MODEL.encode(
            CATALOGUE["combined_text"].tolist(),
            normalize_embeddings=True,
        )
        logger.info(f"Embeddings computed: shape {EMBEDDINGS.shape}")
        logger.info("Startup complete. API ready to serve requests.")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise RuntimeError(f"Failed to initialize API: {e}") from e


@app.get("/health", tags=["Health"])
def health() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        Dict with status information indicating API is operational.
        
    Example:
        >>> GET /health
        {"status": "healthy"}
    """
    return {"status": "healthy"}


@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
def index(request: Request) -> HTMLResponse:
    """
    Web UI endpoint for interactive testing.
    
    Serves a simple HTML interface where users can input job descriptions
    and receive assessment recommendations.
    
    Args:
        request: FastAPI Request object for template rendering.
        
    Returns:
        HTMLResponse: Rendered index.html template.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/recommend", response_model=RecommendResponse, tags=["Recommendations"])
def recommend(payload: RecommendRequest) -> RecommendResponse:
    """
    Main recommendation endpoint.
    
    Takes a natural language query or job description URL and returns
    the most relevant SHL Individual Test Solutions assessments.
    
    The endpoint ensures:
    - Minimum 5 recommendations (if available in catalogue)
    - Maximum 10 recommendations
    - Balanced selection across test type categories
    - High semantic relevance to the query
    
    Args:
        payload: Request containing the job description query.
        
    Returns:
        RecommendResponse: List of recommended assessments with metadata.
        
    Raises:
        HTTPException: 
            - 400 if query is empty
            - 500 if no assessments are available or system error occurs
            
    Example:
        >>> POST /recommend
        {"query": "Java developer with strong problem-solving skills"}
        {
          "recommended_assessments": [
            {
              "url": "https://...",
              "name": "Core Java Assessment",
              ...
            }
          ]
        }
    """
    if MODEL is None or CATALOGUE is None or EMBEDDINGS is None:
        logger.error("API not initialized - resources not loaded")
        raise HTTPException(
            status_code=503,
            detail="Service unavailable: API not fully initialized"
        )
    
    query = payload.query.strip()
    if not query:
        logger.warning("Empty query received")
        raise HTTPException(
            status_code=400,
            detail="Query must be a non-empty string"
        )

    try:
        # Get recommendations (request up to 10, but ensure minimum 5)
        logger.info(f"Processing recommendation request: {query[:50]}...")
        results = recommend_assessments(
            catalogue=CATALOGUE,
            assessment_embeddings=EMBEDDINGS,
            model=MODEL,
            job_description=query,
            top_k=config.DEFAULT_TOP_K,
        )

        if results.empty:
            logger.error("No assessments returned from recommendation engine")
            raise HTTPException(
                status_code=500,
                detail="No assessments available"
            )

        # Ensure minimum 5 recommendations (requirement: minimum 5, maximum 10)
        # If balanced selection returned fewer than 5, get top-k by similarity to fill
        if len(results) < config.MIN_RECOMMENDATIONS:
            logger.info(
                f"Only {len(results)} recommendations found, "
                f"falling back to similarity-based selection"
            )
            # Get top recommendations by similarity (without balanced selection)
            query_embedding = MODEL.encode(
                query,
                normalize_embeddings=True,
            ).reshape(1, -1)
            similarities = cosine_similarity(query_embedding, EMBEDDINGS)[0]
            
            # Get top 10 by similarity
            top_indices = similarities.argsort()[-config.MAX_RECOMMENDATIONS:][::-1]
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
                    if len(results) + len(additional_results) >= config.MAX_RECOMMENDATIONS:
                        break
            
            # Combine results
            if additional_results:
                additional_df = pd.DataFrame(additional_results)
                results = pd.concat([results, additional_df], ignore_index=True)
            
            # Ensure we have at least MIN_RECOMMENDATIONS (or as many as available if catalogue is small)
            min_results = min(config.MIN_RECOMMENDATIONS, len(CATALOGUE))
            if len(results) < min_results:
                # If still not enough, take top by similarity
                top_indices = similarities.argsort()[-min_results:][::-1]
                results = CATALOGUE.iloc[top_indices].copy()
                results["relevance_score"] = similarities[top_indices]
                results = results.reset_index(drop=True)

        # Limit to maximum 10
        results = results.head(config.MAX_RECOMMENDATIONS)
        
        logger.info(f"Returning {len(results)} recommendations")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing recommendation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        ) from e

    # Convert DataFrame rows to response models
    recs: List[AssessmentResponse] = []
    for _, row in results.iterrows():
        try:
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
        except (ValueError, KeyError) as e:
            logger.warning(f"Skipping invalid assessment row: {e}")
            continue

    if not recs:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate valid recommendations"
        )

    return RecommendResponse(recommended_assessments=recs)


