from pathlib import Path
from typing import List

import pandas as pd


CATALOGUE_CSV = Path("data") / "catalogue.csv"


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
    Load the SHL Individual Test Solutions catalogue.

    Expected CSV columns (at minimum):
        - url
        - name
        - description
        - adaptive_support
        - duration   (minutes, integer)
        - remote_support
        - test_type  (pipe‑separated string, e.g. "Knowledge & Skills|Personality & Behavior")

    The function will also add convenient helper columns like
    - duration_minutes
    - combined_text
    """
    if not CATALOGUE_CSV.exists():
        # Fall back to a tiny in‑memory catalogue so that the UI
        # still works while the user is developing the scraper.
        return _load_sample_catalogue()

    df = pd.read_csv(CATALOGUE_CSV)

    # Normalise test_type into a list[str]
    if "test_type" in df.columns:
        df["test_type"] = df["test_type"].apply(_parse_test_type)
    else:
        df["test_type"] = [[] for _ in range(len(df))]

    _add_derived_fields(df)
    return df
