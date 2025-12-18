import streamlit as st
import pandas as pd
from pathlib import Path

from data.catalogue import load_catalogue
from models.embedding_model import load_embedding_model
from recommender.engine import recommend_assessments
from utils.text_utils import is_valid_text

# -----------------------------
# App config
# -----------------------------
st.set_page_config(
    page_title="SHL Assessment Recommendation Engine",
    layout="centered"
)

st.title("SHL Assessment Recommendation Engine")
st.write("Recommend the most suitable SHL assessments based on job requirements.")

# -----------------------------
# Load data and model
# -----------------------------
@st.cache_resource
def init_model():
    return load_embedding_model()

@st.cache_data
def init_catalogue():
    return load_catalogue()


@st.cache_data
def load_example_queries():
    """
    Load example queries from the provided SHL Gen_AI dataset (if present)
    so users can quickly test the recommender.
    """
    xlsx_path = Path("Gen_AI Dataset.xlsx")
    if not xlsx_path.exists():
        return None

    try:
        df = pd.read_excel(xlsx_path)
        # Keep only the relevant columns if they exist
        expected_cols = [c for c in ["Query", "Assessment_url"] if c in df.columns]
        return df[expected_cols]
    except Exception:
        # If anything goes wrong, just return None and fall back to manual input
        return None

model = init_model()
catalogue = init_catalogue()
example_df = load_example_queries()

@st.cache_data
def compute_embeddings(texts):
    return model.encode(texts, normalize_embeddings=True)

assessment_embeddings = compute_embeddings(
    catalogue["combined_text"].tolist()
)

# -----------------------------
# UI
# -----------------------------
prefill_text = ""
ground_truth_url = None

if example_df is not None:
    with st.expander("Use example queries from SHL Gen_AI dataset"):
        example_options = ["(None)"] + example_df["Query"].tolist()
        selected = st.selectbox("Example queries", example_options, index=0)
        if selected != "(None)":
            prefill_text = selected
            # Retrieve corresponding URL if present
            match = example_df[example_df["Query"] == selected]
            if "Assessment_url" in example_df.columns and not match.empty:
                ground_truth_url = match["Assessment_url"].iloc[0]

job_description = st.text_area(
    "Job Description",
    value=prefill_text,
    placeholder="e.g. Software Engineer role requiring strong problem solving and programming skills"
)

col1, col2 = st.columns(2)

with col1:
    assessment_type = st.selectbox(
        "Preferred Assessment Type",
        ["Any", "Cognitive Ability", "Personality", "Technical Skill", "Behavioral"]
    )

with col2:
    max_duration = st.slider(
        "Maximum Duration (minutes)",
        10, 60, 60
    )

top_k = st.slider("Number of Recommendations", 1, 5, 3)

# -----------------------------
# Run recommender
# -----------------------------
if st.button("Recommend Assessments"):
    if not is_valid_text(job_description):
        st.warning("Please enter a valid job description.")
    else:
        results = recommend_assessments(
            catalogue=catalogue,
            assessment_embeddings=assessment_embeddings,
            model=model,
            job_description=job_description,
            top_k=top_k,
            max_duration=max_duration,
            preferred_type=assessment_type
        )

        st.subheader("Recommended Assessments")

        # If we have a labelled ground-truth assessment URL for this query,
        # show it at the top so users can compare with the recommendations.
        if ground_truth_url:
            st.markdown(
                f"**Ground-truth assessment URL from dataset:** "
                f"[{ground_truth_url}]({ground_truth_url})"
            )
            st.divider()

        for _, row in results.iterrows():
            st.markdown(f"### {row['name']}")
            if "url" in row and isinstance(row["url"], str) and row["url"]:
                st.markdown(f"[View assessment]({row['url']})")
            st.write(row["description"])
            st.write(f"**Type:** {row['type']}")
            st.write(f"**Duration:** {row['duration_minutes']} minutes")
            st.write(f"**Relevance Score:** {row['relevance_score']:.3f}")
            st.divider()
