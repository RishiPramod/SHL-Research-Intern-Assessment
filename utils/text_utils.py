"""
Text processing utilities for URL extraction and validation.

This module provides functions for:
- Validating text input
- Detecting URLs in text
- Extracting readable text from HTML pages
"""
import logging
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)

# URL pattern matching
URL_REGEX = re.compile(r"^https?://", re.IGNORECASE)


def is_valid_text(text: Optional[str]) -> bool:
    """
    Check if text is valid (non-empty after stripping).
    
    Args:
        text: Text string to validate.
        
    Returns:
        bool: True if text is non-empty, False otherwise.
        
    Example:
        >>> is_valid_text("  Hello  ")
        True
        >>> is_valid_text("")
        False
        >>> is_valid_text(None)
        False
    """
    return text is not None and len(text.strip()) > 0


def is_likely_url(text: str) -> bool:
    """
    Check if text appears to be a URL.
    
    Args:
        text: Text string to check.
        
    Returns:
        bool: True if text starts with http:// or https://, False otherwise.
        
    Example:
        >>> is_likely_url("https://example.com/job")
        True
        >>> is_likely_url("Java developer needed")
        False
    """
    if not text:
        return False
    return bool(URL_REGEX.match(text.strip()))


def extract_text_from_url(url: str, timeout: Optional[int] = None) -> str:
    """
    Fetch URL and extract readable text from HTML.
    
    This function is intentionally lightweight - it's designed to extract
    job description text from web pages for embedding, not as a comprehensive
    web scraper.
    
    Args:
        url: URL to fetch and extract text from.
        timeout: Request timeout in seconds (defaults to config value).
        
    Returns:
        str: Extracted text content, or empty string if extraction fails.
        
    Example:
        >>> text = extract_text_from_url("https://example.com/job-posting")
        >>> len(text) > 0
        True
    """
    if timeout is None:
        timeout = config.URL_EXTRACTION_TIMEOUT
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; SHL-Recommendation-Bot/1.0)'
        }
        resp = requests.get(url, timeout=timeout, headers=headers)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout while fetching URL: {url}")
        return ""
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error fetching URL {url}: {e}")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error fetching URL {url}: {e}")
        return ""

    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Remove script, style, and noscript tags
        for tag in soup(["script", "style", "noscript", "meta", "link"]):
            tag.decompose()
        
        # Extract text and normalize whitespace
        text = " ".join(soup.get_text(separator=" ").split())
        
        if not text or len(text) < 10:
            logger.warning(f"Extracted text from {url} is too short or empty")
            return ""
        
        logger.info(f"Successfully extracted {len(text)} characters from {url}")
        return text
        
    except Exception as e:
        logger.error(f"Error parsing HTML from {url}: {e}")
        return ""
