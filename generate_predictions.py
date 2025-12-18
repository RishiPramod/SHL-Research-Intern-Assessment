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
        
        # Get top 10 recommendations
        results = recommend_assessments(
            catalogue=catalogue,
            assessment_embeddings=assessment_embeddings,
            model=model,
            job_description=query,
            top_k=10,
        )
        
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
