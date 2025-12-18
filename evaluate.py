"""
Evaluation script to calculate Mean Recall@K metric.

This script:
1. Loads the labeled train data
2. Generates recommendations for each query
3. Calculates Recall@K for each query
4. Computes Mean Recall@K across all queries
"""
import pandas as pd
from pathlib import Path
from data.catalogue import load_catalogue
from models.embedding_model import load_embedding_model
from recommender.engine import recommend_assessments


def normalize_url(url):
    """
    Normalize URL for comparison by extracting the assessment slug.
    
    Handles both formats:
    - /products/product-catalog/view/assessment-name/
    - /solutions/products/product-catalog/view/assessment-name/
    """
    if pd.isna(url) or not url:
        return None
    url = str(url).strip()
    # Extract the slug (last part before trailing slash)
    # e.g., "automata-fix-new" from ".../view/automata-fix-new/"
    if '/view/' in url:
        parts = url.split('/view/')
        if len(parts) > 1:
            slug = parts[1].rstrip('/')
            return slug.lower()
    return url.lower()


def calculate_recall_at_k(recommended_urls, relevant_urls, k=10):
    """
    Calculate Recall@K for a single query.
    
    Args:
        recommended_urls: List of recommended assessment URLs (top K)
        relevant_urls: Set of relevant assessment URLs (ground truth)
        k: Number of top recommendations to consider
    
    Returns:
        Recall@K value (float between 0 and 1)
    """
    if not relevant_urls:
        return 0.0
    
    # Normalize URLs for comparison
    normalized_relevant = {normalize_url(url) for url in relevant_urls if normalize_url(url)}
    normalized_recommended = [normalize_url(url) for url in recommended_urls[:k] if normalize_url(url)]
    
    # Count how many relevant assessments are in top k
    relevant_in_top_k = sum(1 for url in normalized_recommended if url in normalized_relevant)
    
    # Recall@K = relevant in top K / total relevant
    recall = relevant_in_top_k / len(normalized_relevant) if normalized_relevant else 0.0
    return recall


def evaluate_mean_recall_at_k(k=10, train_data_path=None):
    """
    Evaluate the recommendation system using Mean Recall@K metric.
    
    Args:
        k: Number of top recommendations to consider (default: 10)
        train_data_path: Path to labeled train data Excel file
    
    Returns:
        Dictionary with evaluation results
    """
    print("=" * 60)
    print(f"Evaluating Mean Recall@{k}")
    print("=" * 60)
    
    # Load model and catalogue
    print("\n1. Loading model and catalogue...")
    model = load_embedding_model()
    catalogue = load_catalogue()
    
    # Check catalogue size
    print(f"   Catalogue contains {len(catalogue)} assessments")
    if len(catalogue) < 377:
        print(f"   WARNING: Catalogue has only {len(catalogue)} assessments.")
        print("   Expected at least 377 Individual Test Solutions.")
        print("   Please ensure you have scraped the SHL website catalogue.")
    if len(catalogue) < 10:
        print("   ERROR: Catalogue too small for meaningful evaluation.")
        return None
    
    # Pre-compute embeddings
    print("2. Pre-computing embeddings...")
    assessment_embeddings = model.encode(
        catalogue["combined_text"].tolist(),
        normalize_embeddings=True,
    )
    
    # Load labeled train data
    if train_data_path is None:
        train_data_path = Path("Gen_AI Dataset.xlsx")
    
    if not train_data_path.exists():
        raise FileNotFoundError(f"Train data not found: {train_data_path}")
    
    print(f"3. Loading labeled train data from {train_data_path}...")
    df = pd.read_excel(train_data_path)
    
    # Identify columns
    query_col = None
    assessment_url_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'query' in col_lower or 'text' in col_lower or 'job' in col_lower:
            query_col = col
        if 'assessment' in col_lower and 'url' in col_lower:
            assessment_url_col = col
    
    if query_col is None:
        query_col = df.columns[0]
        print(f"   Using first column as queries: {query_col}")
    else:
        print(f"   Found query column: {query_col}")
    
    if assessment_url_col is None:
        # Try to find assessment URL column
        for col in df.columns:
            if col != query_col and 'url' in col.lower():
                assessment_url_col = col
                break
    
    if assessment_url_col is None:
        raise ValueError("Could not find assessment URL column in train data")
    
    print(f"   Found assessment URL column: {assessment_url_col}")
    
    # Group by query to get relevant assessments for each query
    print("\n4. Processing queries and ground truth...")
    query_results = []
    
    for query in df[query_col].dropna().unique():
        # Get relevant assessments for this query (ground truth)
        query_rows = df[df[query_col] == query]
        relevant_urls = set(query_rows[assessment_url_col].dropna().tolist())
        
        if not relevant_urls:
            print(f"   Warning: No ground truth for query: {query[:50]}...")
            continue
        
        # Generate recommendations
        results = recommend_assessments(
            catalogue=catalogue,
            assessment_embeddings=assessment_embeddings,
            model=model,
            job_description=query,
            top_k=k,
        )
        
        # Get recommended URLs
        recommended_urls = results["url"].tolist()
        
        # Calculate Recall@K (with URL normalization)
        recall = calculate_recall_at_k(recommended_urls, relevant_urls, k)
        
        # Count matches with normalization
        normalized_relevant = {normalize_url(url) for url in relevant_urls if normalize_url(url)}
        normalized_recommended = [normalize_url(url) for url in recommended_urls[:k] if normalize_url(url)]
        relevant_in_top_k = sum(1 for url in normalized_recommended if url in normalized_relevant)
        
        query_results.append({
            "query": query,
            "recall@k": recall,
            "relevant_count": len(relevant_urls),
            "recommended_count": len(recommended_urls),
            "relevant_in_top_k": relevant_in_top_k
        })
        
        print(f"   Query: {query[:50]}...")
        print(f"      Relevant: {len(relevant_urls)}, Recommended: {len(recommended_urls)}")
        print(f"      Relevant in top {k}: {query_results[-1]['relevant_in_top_k']}")
        print(f"      Recall@{k}: {recall:.4f}")
    
    # Calculate Mean Recall@K
    if not query_results:
        raise ValueError("No valid queries found in train data")
    
    mean_recall = sum(r["recall@k"] for r in query_results) / len(query_results)
    
    # Print results
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"\nNumber of queries evaluated: {len(query_results)}")
    print(f"K (top recommendations): {k}")
    print(f"\nMean Recall@{k}: {mean_recall:.4f}")
    print(f"\nPer-query Recall@{k}:")
    for i, result in enumerate(query_results, 1):
        print(f"  {i}. {result['recall@k']:.4f} - {result['query'][:50]}...")
    
    # Summary statistics
    print(f"\nSummary Statistics:")
    print(f"  Min Recall@{k}: {min(r['recall@k'] for r in query_results):.4f}")
    print(f"  Max Recall@{k}: {max(r['recall@k'] for r in query_results):.4f}")
    print(f"  Mean Recall@{k}: {mean_recall:.4f}")
    
    return {
        "mean_recall@k": mean_recall,
        "k": k,
        "num_queries": len(query_results),
        "per_query_results": query_results
    }


if __name__ == "__main__":
    # Evaluate with K=10 (as per requirements: up to 10 recommendations)
    results = evaluate_mean_recall_at_k(k=10)
    
    print("\n" + "=" * 60)
    print("Evaluation complete!")
    print("=" * 60)
