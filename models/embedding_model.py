"""
Embedding model loader for semantic similarity computation.

This module provides functionality to load and initialize the sentence transformer
model used for generating dense vector representations of text.
"""
from sentence_transformers import SentenceTransformer

import config


def load_embedding_model() -> SentenceTransformer:
    """
    Load and return the sentence transformer embedding model.
    
    The model is initialized once and can be reused across multiple
    embedding computations for efficiency.
    
    Returns:
        SentenceTransformer: Initialized sentence transformer model.
        
    Example:
        >>> model = load_embedding_model()
        >>> embeddings = model.encode(["Sample text"], normalize_embeddings=True)
        >>> embeddings.shape
        (1, 384)
    """
    return SentenceTransformer(config.EMBEDDING_MODEL_NAME)
