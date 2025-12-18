"""
Generate predictions CSV file for submission.

This script loads test queries from the Excel dataset and generates recommendations
using the recommendation engine, outputting results in the required CSV format.
"""
import logging
from pathlib import Path

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

import config
from data.catalogue import load_catalogue
from models.embedding_model import load_embedding_model
from recommender.engine import recommend_assessments

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_predictions_csv() -> pd.DataFrame:
    """
    Generate predictions CSV in the required format for submission.
    
    Loads test queries from the Excel file, generates recommendations for each query,
    and saves results to predictions.csv with columns: Query, Assessment_url.
    
    Returns:
        pd.DataFrame: DataFrame containing predictions, or None if generation fails.
        
    Raises:
        FileNotFoundError: If the test dataset Excel file is not found.
    """
    logger.info("Loading model and catalogue...")
    model = load_embedding_model()
    catalogue = load_catalogue()
    
    # Check catalogue size
    logger.info(f"Catalogue contains {len(catalogue)} assessments")
    if len(catalogue) < config.MIN_CATALOGUE_SIZE:
        logger.warning(
            f"Catalogue has only {len(catalogue)} assessments. "
            f"Expected at least {config.MIN_CATALOGUE_SIZE} Individual Test Solutions."
        )
        if len(catalogue) < 10:
            logger.error("Catalogue too small. Cannot generate proper recommendations.")
            return None
    
    # Pre-compute embeddings
    logger.info("Pre-computing embeddings...")
    assessment_embeddings = model.encode(
        catalogue["combined_text"].tolist(),
        normalize_embeddings=True,
    )
    logger.info(f"Embeddings computed: shape {assessment_embeddings.shape}")
    
    # Load test queries from Excel file
    xlsx_path = Path("Gen_AI Dataset.xlsx")
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Test dataset not found: {xlsx_path}")
    
    logger.info(f"Loading test queries from {xlsx_path}...")
    df = pd.read_excel(xlsx_path)
    
    # Identify query column (could be "Query" or similar)
    query_col = None
    for col in df.columns:
        if 'query' in col.lower() or 'text' in col.lower() or 'job' in col.lower():
            query_col = col
            break
    
    if query_col is None:
        # If no query column found, assume first column
        query_col = df.columns[0]
        logger.info(f"Using first column as queries: {query_col}")
    else:
        logger.info(f"Using query column: {query_col}")
    
    # Get unique queries (test set)
    queries = df[query_col].dropna().unique()
    logger.info(f"Found {len(queries)} unique test queries")
    
    # Generate predictions
    predictions = []
    for i, query in enumerate(queries, 1):
        logger.info(f"Processing query {i}/{len(queries)}: {query[:50]}...")
        
        try:
            # Get top 10 recommendations (minimum 5, maximum 10)
            results = recommend_assessments(
                catalogue=catalogue,
                assessment_embeddings=assessment_embeddings,
                model=model,
                job_description=query,
                top_k=config.DEFAULT_TOP_K,
            )
            
            # Ensure minimum 5 recommendations
            if len(results) < config.MIN_RECOMMENDATIONS:
                logger.info(
                    f"Only {len(results)} recommendations found, "
                    "using similarity-based fallback"
                )
                # Get additional recommendations by similarity
                query_embedding = model.encode(
                    query,
                    normalize_embeddings=True,
                ).reshape(1, -1)
                similarities = cosine_similarity(query_embedding, assessment_embeddings)[0]
                
                # Get top 10 by similarity
                top_indices = similarities.argsort()[-config.MAX_RECOMMENDATIONS:][::-1]
                fallback_results = catalogue.iloc[top_indices].copy()
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
                
                # Ensure we have at least MIN_RECOMMENDATIONS (or as many as available)
                min_results = min(config.MIN_RECOMMENDATIONS, len(catalogue))
                if len(results) < min_results:
                    top_indices = similarities.argsort()[-min_results:][::-1]
                    results = catalogue.iloc[top_indices].copy()
                    results["relevance_score"] = similarities[top_indices]
                    results = results.reset_index(drop=True)
            
            # Limit to maximum 10
            results = results.head(config.MAX_RECOMMENDATIONS)
            
            # Add each recommendation to predictions
            for _, row in results.iterrows():
                predictions.append({
                    "Query": query,
                    "Assessment_url": row.get("url", "")
                })
                
        except Exception as e:
            logger.error(f"Error processing query {i}: {e}", exc_info=True)
            continue
    
    # Create DataFrame
    predictions_df = pd.DataFrame(predictions)
    
    # Save to CSV
    output_path = "predictions.csv"
    predictions_df.to_csv(output_path, index=False)
    logger.info(f"\nPredictions saved to: {output_path}")
    logger.info(f"Total predictions: {len(predictions_df)}")
    logger.info(f"Unique queries: {predictions_df['Query'].nunique()}")
    
    return predictions_df

if __name__ == "__main__":
    generate_predictions_csv()
