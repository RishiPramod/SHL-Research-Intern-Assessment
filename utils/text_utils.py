from __future__ import annotations

import re
from typing import Optional

import requests
from bs4 import BeautifulSoup


URL_REGEX = re.compile(r"^https?://", re.IGNORECASE)


def is_valid_text(text: Optional[str]) -> bool:
    return text is not None and len(text.strip()) > 0


def is_likely_url(text: str) -> bool:
    if not text:
        return False
    return bool(URL_REGEX.match(text.strip()))


def extract_text_from_url(url: str, timeout: int = 10) -> str:
    """
    Fetch the URL and extract readable text from HTML.

    This is intentionally lightweight – it's only meant to turn a JD
    web page into plain text for embedding, not to be a perfect scraper.
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except Exception:
        return ""

    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove script / style tags
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())
        return text
    except Exception:
        return ""
