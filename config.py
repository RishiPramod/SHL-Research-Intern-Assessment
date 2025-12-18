"""
Configuration constants for the SHL Assessment Recommendation System.
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
CATALOGUE_CSV_PATH = BASE_DIR / "data" / "catalogue.csv"
TEMPLATES_DIR = BASE_DIR / "templates"

# Model Configuration
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Recommendation Configuration
MIN_RECOMMENDATIONS = 5
MAX_RECOMMENDATIONS = 10
DEFAULT_TOP_K = 10

# API Configuration
API_TITLE = "SHL Assessment Recommendation API"
API_VERSION = "1.0.0"
CORS_ORIGINS = ["*"]  # In production, specify actual frontend URLs

# URL Extraction Configuration
URL_EXTRACTION_TIMEOUT = 10  # seconds

# Catalogue Requirements
MIN_CATALOGUE_SIZE = 377
