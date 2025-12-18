"""
Core recommendation engine for SHL Assessment Recommendation System.

This module implements the semantic similarity-based recommendation algorithm
that matches job descriptions to relevant SHL Individual Test Solutions assessments.
"""
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from utils.text_utils import extract_text_from_url, is_likely_url


TEST_TYPE_DISPLAY_MAP = {
    "Cognitive Ability": ["Ability & Aptitude"],
    "Personality": ["Personality & Behavior"],
    "Technical Skill": ["Knowledge & Skills"],
    "Behavioral": ["Competencies", "Personality & Behavior"],
}


def _maybe_expand_query_text(job_description: str) -> str:
    """
    If the query looks like a URL, try to download and extract the
    visible text so that we can embed the JD instead of the raw URL.
    """
    if not is_likely_url(job_description):
        return job_description

    extracted = extract_text_from_url(job_description)
    return extracted if extracted else job_description


def _bucket_by_test_type(
    catalogue: pd.DataFrame,
    similarities: np.ndarray,
    needed_types: List[str]
) -> Dict[str, List[int]]:
    """
    Bucket ranked indices by whether their test_type overlaps with
    the requested / inferred SHL test type categories.
    """
    ranked_idx = np.argsort(-similarities)  # descending

    buckets = {tt: [] for tt in needed_types}
    buckets["other"] = []

    for idx in ranked_idx:
        row_types: Iterable[str] = catalogue.iloc[idx]["test_type"]
        row_types_set = set(row_types) if isinstance(row_types, list) else set()

        placed = False
        for tt in needed_types:
            if tt in row_types_set:
                buckets[tt].append(idx)
                placed = True
                break

        if not placed:
            buckets["other"].append(idx)

    return buckets


def _balanced_select(buckets: Dict[str, List[int]], top_k: int) -> List[int]:
    """
    Round‑robin selection from buckets to ensure a balanced mix
    across the requested test types, with a fallback to the "other"
    bucket if we still need more results.
    """
    selected: List[int] = []
    keys = [k for k in buckets.keys() if k != "other"]
    cursors = {k: 0 for k in keys}

    # First pass: round‑robin across the main buckets
    while len(selected) < top_k and any(cursors[k] < len(buckets[k]) for k in keys):
        for k in keys:
            if cursors[k] < len(buckets[k]):
                selected.append(buckets[k][cursors[k]])
                cursors[k] += 1
                if len(selected) == top_k:
                    break

    # Second pass: fill from "other" bucket if needed
    if len(selected) < top_k:
        for idx in buckets.get("other", []):
            if idx not in selected:
                selected.append(idx)
                if len(selected) == top_k:
                    break

    return selected


def _infer_needed_test_types(query: str) -> List[str]:
    """
    Very lightweight heuristic to infer which SHL test_type
    categories are relevant from the query text.
    """
    q = query.lower()
    needed: List[str] = []

    if any(k in q for k in ["cognitive", "aptitude", "ability", "reasoning"]):
        needed.append("Ability & Aptitude")

    if any(k in q for k in ["personality", "behavior", "behaviour", "competency", "competencies"]):
        needed.append("Personality & Behavior")

    if any(k in q for k in ["coding", "developer", "engineer", "programming", "python", "java", "sql", "technical"]):
        needed.append("Knowledge & Skills")

    # Fallback: if nothing inferred, treat as no special requirement
    return list(dict.fromkeys(needed))  # remove duplicates while preserving order


def recommend_assessments(
    catalogue: pd.DataFrame,
    assessment_embeddings: np.ndarray,
    model: SentenceTransformer,
    job_description: str,
    top_k: int = 3,
    max_duration: Optional[int] = None,
    preferred_type: Optional[str] = None,
) -> pd.DataFrame:
    """
    Core recommendation function for matching job descriptions to assessments.
    
    This function implements a semantic similarity-based recommendation algorithm
    with the following steps:
    1. Embeds the query (or extracts text from JD URL)
    2. Computes cosine similarity against all pre-computed assessment embeddings
    3. Applies duration and type filters if specified
    4. Balances results across relevant SHL test_type buckets for diversity
    
    Args:
        catalogue: DataFrame containing assessment metadata.
        assessment_embeddings: Pre-computed embeddings for all assessments (numpy array).
        model: Sentence transformer model for encoding queries.
        job_description: Natural language query or URL to job description.
        top_k: Maximum number of recommendations to return (default: 3).
        max_duration: Optional maximum assessment duration in minutes.
        preferred_type: Optional preferred assessment type filter.
        
    Returns:
        pd.DataFrame: DataFrame with recommended assessments, sorted by relevance_score.
        Columns include: url, name, description, duration, test_type, relevance_score, etc.
        
    Example:
        >>> results = recommend_assessments(
        ...     catalogue=df,
        ...     assessment_embeddings=embeddings,
        ...     model=model,
        ...     job_description="Java developer",
        ...     top_k=10
        ... )
        >>> len(results)
        10
    """
    # 1. Prepare query text
    query_text = _maybe_expand_query_text(job_description)

    # 2. Embed query
    query_embedding = model.encode(
        query_text,
        normalize_embeddings=True,
    ).reshape(1, -1)

    # 3. Similarity against all assessments
    similarities = cosine_similarity(
        query_embedding,
        assessment_embeddings,
    )[0]

    # 4. Build working frame
    results = catalogue.copy().reset_index(drop=True)
    results["relevance_score"] = similarities

    # 5. Apply filters
    if max_duration is not None:
        results = results[results["duration_minutes"] <= max_duration]

    if preferred_type and preferred_type != "Any" and "type" in results.columns:
        results = results[results["type"] == preferred_type]

    if results.empty:
        # No matches after filters – fall back to global top_k
        base = catalogue.copy().reset_index(drop=True)
        base["relevance_score"] = similarities
        base = base.sort_values(by="relevance_score", ascending=False)
        return base.head(top_k)

    # 6. Balanced selection by SHL test_type (Ability & Aptitude, etc.)
    needed_types = _infer_needed_test_types(query_text)

    # If the user explicitly chose a preferred_type in the UI and we
    # can map it to an SHL test_type, treat that as the only needed type.
    if preferred_type and preferred_type != "Any":
        mapped = TEST_TYPE_DISPLAY_MAP.get(preferred_type)
        if mapped:
            needed_types = mapped

    # If still nothing inferred, just return sorted by relevance
    if not needed_types or "test_type" not in results.columns:
        results = results.sort_values(by="relevance_score", ascending=False)
        return results.head(top_k)

    # Compute buckets using only the filtered subset
    subset_similarities = results["relevance_score"].to_numpy()
    buckets = _bucket_by_test_type(results, subset_similarities, needed_types)
    selected_indices = _balanced_select(buckets, top_k)

    # Map local indices back to the results DataFrame
    final = results.iloc[selected_indices].copy()
    final = final.sort_values(by="relevance_score", ascending=False)
    return final.head(top_k)
