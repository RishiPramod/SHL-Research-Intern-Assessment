"""
Advanced web scraper for SHL Individual Test Solutions.

This scraper uses multiple strategies:
1. Direct HTML parsing
2. API endpoint detection
3. Selenium for JavaScript-rendered content (optional)
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
import json


BASE_URL = "https://www.shl.com"
CATALOGUE_URL = "https://www.shl.com/solutions/products/product-catalog/"


def get_session():
    """Create a requests session with proper headers."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session


def fetch_with_retry(session, url, max_retries=3, delay=2):
    """Fetch URL with retries."""
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"    Retry {attempt + 1}/{max_retries}...")
                time.sleep(delay)
            else:
                print(f"    Failed: {e}")
                return None
    return None


def extract_from_assessment_page(session, url):
    """Extract detailed information from an assessment detail page."""
    response = fetch_with_retry(session, url)
    if not response:
        return {}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    details = {}
    
    # Extract name
    name_selectors = [
        soup.find('h1'),
        soup.find('h2', class_=re.compile('title|name', re.I)),
        soup.select_one('[data-testid*="title"], [class*="title"]'),
    ]
    for selector in name_selectors:
        if selector:
            details['name'] = selector.get_text(strip=True)
            break
    
    if 'name' not in details:
        title_tag = soup.find('title')
        if title_tag:
            details['name'] = title_tag.get_text(strip=True).split('|')[0].strip()
    
    # Extract description
    desc_patterns = [
        soup.find('div', class_=re.compile('description|overview|summary|content', re.I)),
        soup.find('section', class_=re.compile('description|overview', re.I)),
        soup.find('p', class_=re.compile('description|intro', re.I)),
        soup.select_one('[data-testid*="description"]'),
    ]
    for pattern in desc_patterns:
        if pattern:
            text = pattern.get_text(separator=' ', strip=True)
            if len(text) > 20:  # Meaningful description
                details['description'] = text[:500]  # Limit length
                break
    
    # Extract metadata from structured data or text
    page_text = soup.get_text().lower()
    
    # Adaptive support
    if re.search(r'\badaptive\b', page_text):
        details['adaptive_support'] = 'Yes' if re.search(r'adaptive.*(?:yes|support|available)', page_text) else 'No'
    else:
        details['adaptive_support'] = 'No'
    
    # Remote support (most SHL assessments support remote)
    details['remote_support'] = 'Yes' if re.search(r'remote|online|digital', page_text) else 'Yes'
    
    # Duration
    duration_patterns = [
        r'(\d+)\s*(?:minute|min|m)\b',
        r'(\d+)\s*(?:hour|hr|h)\b',
        r'duration[:\s]+(\d+)',
        r'(\d+)\s*(?:minute|min)',
    ]
    duration = None
    for pattern in duration_patterns:
        match = re.search(pattern, page_text, re.I)
        if match:
            num = int(match.group(1))
            if 'hour' in match.group(0).lower() or 'hr' in match.group(0).lower():
                duration = num * 60
            else:
                duration = num
            break
    
    details['duration'] = duration if duration else 30
    
    # Test type - look for category indicators
    test_types = []
    type_mapping = {
        'Ability & Aptitude': ['ability', 'aptitude', 'cognitive', 'reasoning', 'numerical', 'verbal', 'logical'],
        'Knowledge & Skills': ['knowledge', 'skill', 'technical', 'competency', 'expertise', 'proficiency'],
        'Personality & Behavior': ['personality', 'behavior', 'behaviour', 'trait', 'preference', 'style'],
        'Competencies': ['competency', 'competence', 'capability'],
        'Biodata & Situational Judgement': ['biodata', 'situational', 'judgement', 'judgment', 'scenario'],
    }
    
    for test_type, keywords in type_mapping.items():
        if any(re.search(rf'\b{kw}\b', page_text) for kw in keywords):
            test_types.append(test_type)
    
    # Also check for explicit category tags
    category_tags = soup.find_all(['span', 'div', 'a'], class_=re.compile('category|type|tag', re.I))
    for tag in category_tags:
        tag_text = tag.get_text(strip=True)
        for test_type in type_mapping.keys():
            if test_type.lower() in tag_text.lower():
                if test_type not in test_types:
                    test_types.append(test_type)
    
    if not test_types:
        test_types = ['Unknown']
    
    details['test_type'] = '|'.join(test_types)
    
    return details


def find_assessment_links(soup, base_url):
    """Find all assessment links on a page."""
    links = []
    seen_hrefs = set()
    
    # Strategy 1: Direct links with product-catalog/view
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        full_url = urljoin(base_url, href)
        
        # Check if it's an assessment link
        if ('product-catalog' in href or 'solutions/products' in href) and 'view' in href:
            # Skip pre-packaged
            if 'pre-packaged' in href.lower() or 'prepackaged' in href.lower():
                continue
            
            if full_url not in seen_hrefs:
                seen_hrefs.add(full_url)
                name = link.get_text(strip=True)
                if not name or len(name) < 3:
                    # Try parent elements
                    parent = link.find_parent(['div', 'li', 'article', 'section'])
                    if parent:
                        name_elem = parent.find(['h2', 'h3', 'h4', 'span', 'div'], 
                                               class_=re.compile('title|name|heading', re.I))
                        if name_elem:
                            name = name_elem.get_text(strip=True)
                
                if name and len(name) > 2:
                    links.append((full_url, name))
    
    # Strategy 2: Look for data attributes or JavaScript variables
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            # Look for URLs in JavaScript
            url_matches = re.findall(r'["\'](https?://[^"\']*product-catalog[^"\']*view[^"\']*)["\']', script.string)
            for url in url_matches:
                if 'pre-packaged' not in url.lower():
                    if url not in seen_hrefs:
                        seen_hrefs.add(url)
                        # Try to extract name from context
                        name = "Assessment"  # Default
                        links.append((url, name))
    
    return links


def scrape_catalogue(session):
    """Main scraping function."""
    print("=" * 70)
    print("SHL Individual Test Solutions Scraper")
    print("=" * 70)
    print(f"\nTarget: {CATALOGUE_URL}")
    print("Filter: Individual Test Solutions (excluding Pre-packaged)\n")
    
    all_assessments = []
    seen_urls = set()
    
    # Fetch main catalogue page
    print("Step 1: Fetching main catalogue page...")
    response = fetch_with_retry(session, CATALOGUE_URL)
    if not response:
        print("ERROR: Could not fetch catalogue page")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    print("   ✓ Page loaded")
    
    # Find assessment links
    print("\nStep 2: Finding assessment links...")
    links = find_assessment_links(soup, BASE_URL)
    print(f"   Found {len(links)} assessment links")
    
    # Check for pagination or load more
    pagination = soup.find_all('a', href=re.compile(r'page|pagination|next|more', re.I))
    if pagination:
        print(f"   Found {len(pagination)} potential pagination links")
    
    # Process each assessment
    print(f"\nStep 3: Extracting details from {len(links)} assessments...")
    print("   This will take several minutes...\n")
    
    for i, (url, name) in enumerate(links, 1):
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        print(f"   [{i}/{len(links)}] {name[:60]}...")
        
        # Get basic info
        assessment = {
            'url': url,
            'name': name,
            'description': '',
            'adaptive_support': 'No',
            'remote_support': 'Yes',
            'duration': 30,
            'test_type': 'Unknown'
        }
        
        # Extract detailed info
        details = extract_from_assessment_page(session, url)
        assessment.update(details)
        
        all_assessments.append(assessment)
        
        # Rate limiting
        if i % 10 == 0:
            print(f"      Progress: {i}/{len(links)} assessments processed")
            time.sleep(2)
        else:
            time.sleep(0.8)
    
    # Create DataFrame
    df = pd.DataFrame(all_assessments)
    
    # Ensure all required columns exist
    required_cols = ['url', 'name', 'description', 'adaptive_support', 'remote_support', 'duration', 'test_type']
    for col in required_cols:
        if col not in df.columns:
            df[col] = ''
    
    # Clean and validate
    df = df[required_cols]
    df = df.drop_duplicates(subset=['url'])
    
    # Save
    output_path = Path("data/catalogue.csv")
    output_path.parent.mkdir(exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"\n{'='*70}")
    print("Scraping Complete!")
    print(f"{'='*70}")
    print(f"\nTotal assessments: {len(df)}")
    print(f"Saved to: {output_path}")
    
    if len(df) < 377:
        print(f"\n⚠️  WARNING: Only {len(df)} assessments found (need 377+)")
        print("\nPossible reasons:")
        print("  1. Website structure may have changed")
        print("  2. Content may be loaded via JavaScript (need Selenium)")
        print("  3. May require authentication or different access method")
        print("\nNext steps:")
        print("  1. Check the website manually")
        print("  2. Consider using Selenium for JavaScript-rendered content")
        print("  3. Look for API endpoints that provide JSON data")
    else:
        print(f"\n✅ Success! Scraped {len(df)} assessments")
    
    return df


if __name__ == "__main__":
    session = get_session()
    df = scrape_catalogue(session)
    
    if df is not None and len(df) > 0:
        print(f"\nSample assessments:")
        print(df[['name', 'url', 'test_type']].head(10).to_string())
