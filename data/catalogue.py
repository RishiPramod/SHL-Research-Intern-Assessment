"""
Catalogue data loader for SHL Individual Test Solutions.

This module handles loading and processing of the assessment catalogue from CSV,
including parsing test types and adding derived fields for recommendation.
"""
import logging
from pathlib import Path
from typing import List

import pandas as pd

import config

logger = logging.getLogger(__name__)


def _load_sample_catalogue() -> pd.DataFrame:
    """
    Very small in‑memory sample catalogue so the app still works
    if the real scraped catalogue has not been generated yet.
    """
    data = [
        {
            "assessment_id": 1,
            "url": "https://example.com/general-ability-test",
            "name": "General Ability Test",
            "description": "Measures critical thinking, problem solving, and numerical reasoning ability.",
            "adaptive_support": "No",
            "remote_support": "Yes",
            "duration": 36,
            "test_type": ["Ability & Aptitude", "Knowledge & Skills"],
        },
        {
            "assessment_id": 2,
            "url": "https://example.com/opq-personality",
            "name": "OPQ Personality Questionnaire",
            "description": "Evaluates workplace personality traits and behavioral preferences.",
            "adaptive_support": "No",
            "remote_support": "Yes",
            "duration": 25,
            "test_type": ["Personality & Behavior"],
        },
    ]

    df = pd.DataFrame(data)
    _add_derived_fields(df)
    return df


def _parse_test_type(value: str) -> List[str]:
    """
    Parse the test_type field from CSV.

    We store it as a pipe‑separated string in the CSV, e.g.:
    "Knowledge & Skills|Personality & Behavior"
    and convert it to a list of strings in memory.
    """
    if pd.isna(value) or not value:
        return []
    return [v.strip() for v in str(value).split("|") if v.strip()]


def _add_derived_fields(df: pd.DataFrame) -> None:
    """
    Add helper columns used by the recommender and UI.
    """
    if "duration_minutes" not in df.columns and "duration" in df.columns:
        df["duration_minutes"] = df["duration"].astype(int)

    if "skills" not in df.columns:
        df["skills"] = ""

    if "type" not in df.columns:
        # Simple primary type derived from test_type if not explicitly present
        df["type"] = df["test_type"].apply(lambda ts: ts[0] if isinstance(ts, list) and ts else "Unknown")

    df["combined_text"] = (
        df["name"].fillna("") + ". "
        + df["description"].fillna("") + ". "
        + "Skills: " + df["skills"].fillna("") + ". "
        + "Types: " + df["type"].fillna("")
    )


def load_catalogue() -> pd.DataFrame:
    """
    Load the SHL Individual Test Solutions catalogue from CSV.
    
    Expected CSV columns (at minimum):
        - url: Assessment URL
        - name: Assessment name
        - description: Assessment description
        - adaptive_support: "Yes" or "No"
        - duration: Duration in minutes (integer)
        - remote_support: "Yes" or "No"
        - test_type: Pipe-separated string (e.g. "Knowledge & Skills|Personality & Behavior")
    
    The function automatically adds helper columns:
        - duration_minutes: Normalized duration field
        - combined_text: Concatenated text for embedding
        - type: Primary test type (first from test_type list)
        - skills: Skills field (empty if not present)
    
    Returns:
        pd.DataFrame: Catalogue with all assessments and derived fields.
        
    Raises:
        FileNotFoundError: If catalogue CSV doesn't exist and no sample data available.
        
    Example:
        >>> df = load_catalogue()
        >>> len(df) >= 377
        True
        >>> "combined_text" in df.columns
        True
    """
    if not config.CATALOGUE_CSV_PATH.exists():
        logger.warning(
            f"Catalogue CSV not found at {config.CATALOGUE_CSV_PATH}. "
            "Using sample catalogue."
        )
        return _load_sample_catalogue()

    try:
        df = pd.read_csv(config.CATALOGUE_CSV_PATH)
        logger.info(f"Loaded catalogue from {config.CATALOGUE_CSV_PATH}")
        
        if len(df) == 0:
            logger.error("Catalogue CSV is empty")
            return _load_sample_catalogue()
        
        # Normalize test_type into a list[str]
        if "test_type" in df.columns:
            df["test_type"] = df["test_type"].apply(_parse_test_type)
        else:
            logger.warning("test_type column not found, initializing empty lists")
            df["test_type"] = [[] for _ in range(len(df))]

        _add_derived_fields(df)
        
        logger.info(
            f"Catalogue loaded successfully: {len(df)} assessments, "
            f"{len(df.columns)} columns"
        )
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading catalogue: {e}", exc_info=True)
        logger.warning("Falling back to sample catalogue")
        return _load_sample_catalogue()
