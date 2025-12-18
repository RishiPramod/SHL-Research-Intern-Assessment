"""
Generate predictions CSV file for submission.
This script loads the test queries and generates recommendations using the recommendation engine.
"""
import pandas as pd
from pathlib import Path
from data.catalogue import load_catalogue
from models.embedding_model import load_embedding_model
from recommender.engine import recommend_assessments

def generate_predictions_csv():
    """Generate predictions CSV in the required format."""
    print("Loading model and catalogue...")
    model = load_embedding_model()
    catalogue = load_catalogue()
    
    # Check catalogue size
    print(f"Catalogue contains {len(catalogue)} assessments")
    if len(catalogue) < 377:
        print(f"WARNING: Catalogue has only {len(catalogue)} assessments.")
        print("Expected at least 377 Individual Test Solutions.")
        print("Please ensure you have scraped the SHL website catalogue.")
        if len(catalogue) < 10:
            print("ERROR: Catalogue too small. Cannot generate proper recommendations.")
            return None
    
    # Pre-compute embeddings
    print("Pre-computing embeddings...")
    assessment_embeddings = model.encode(
        catalogue["combined_text"].tolist(),
        normalize_embeddings=True,
    )
    
    # Load test queries from Excel file
    xlsx_path = Path("Gen_AI Dataset.xlsx")
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Test dataset not found: {xlsx_path}")
    
    print("Loading test queries...")
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
        print(f"Using first column as queries: {query_col}")
    else:
        print(f"Using query column: {query_col}")
    
    # Get unique queries (test set)
    queries = df[query_col].dropna().unique()
    print(f"Found {len(queries)} unique test queries")
    
    # Generate predictions
    predictions = []
    for i, query in enumerate(queries, 1):
        print(f"Processing query {i}/{len(queries)}: {query[:50]}...")
        
        # Get top 10 recommendations (minimum 5, maximum 10)
        results = recommend_assessments(
            catalogue=catalogue,
            assessment_embeddings=assessment_embeddings,
            model=model,
            job_description=query,
            top_k=10,
        )
        
        # Ensure minimum 5 recommendations
        if len(results) < 5:
            # Get additional recommendations by similarity
            from sklearn.metrics.pairwise import cosine_similarity
            query_embedding = model.encode(
                query,
                normalize_embeddings=True,
            ).reshape(1, -1)
            similarities = cosine_similarity(query_embedding, assessment_embeddings)[0]
            
            # Get top 10 by similarity
            top_indices = similarities.argsort()[-10:][::-1]
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
                    if len(results) + len(additional_results) >= 10:
                        break
            
            # Combine results
            if additional_results:
                additional_df = pd.DataFrame(additional_results)
                results = pd.concat([results, additional_df], ignore_index=True)
            
            # Ensure we have at least 5 (or as many as available)
            min_results = min(5, len(catalogue))
            if len(results) < min_results:
                top_indices = similarities.argsort()[-min_results:][::-1]
                results = catalogue.iloc[top_indices].copy()
                results["relevance_score"] = similarities[top_indices]
                results = results.reset_index(drop=True)
        
        # Limit to maximum 10
        results = results.head(10)
        
        # Add each recommendation to predictions
        for _, row in results.iterrows():
            predictions.append({
                "Query": query,
                "Assessment_url": row.get("url", "")
            })
    
    # Create DataFrame
    predictions_df = pd.DataFrame(predictions)
    
    # Save to CSV
    output_path = "predictions.csv"
    predictions_df.to_csv(output_path, index=False)
    print(f"\nPredictions saved to: {output_path}")
    print(f"Total predictions: {len(predictions_df)}")
    print(f"Unique queries: {predictions_df['Query'].nunique()}")
    
    return predictions_df

if __name__ == "__main__":
    generate_predictions_csv()
