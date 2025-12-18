"""
Web scraper to collect Individual Test Solutions from SHL website.

This script:
1. Visits the SHL product catalog
2. Filters for Individual Test Solutions (excludes Pre-packaged Job Solutions)
3. Scrapes assessment details
4. Saves to data/catalogue.csv
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
import json


BASE_URL = "https://www.shl.com"
CATALOGUE_URL = "https://www.shl.com/solutions/products/product-catalog/"


def get_page_content(url, retries=3, delay=2):
    """Fetch page content with retries."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt + 1}/{retries} for {url}")
                time.sleep(delay)
            else:
                print(f"  Failed to fetch {url}: {e}")
                return None
    return None


def extract_assessment_details(assessment_url):
    """Extract detailed information from an assessment page."""
    html = get_page_content(assessment_url)
    if not html:
        return {}
    
    soup = BeautifulSoup(html, 'html.parser')
    details = {}
    
    # Extract name (usually in h1 or title)
    name_elem = soup.find('h1') or soup.find('title')
    if name_elem:
        details['name'] = name_elem.get_text(strip=True)
    
    # Extract description
    desc_selectors = [
        soup.find('div', class_=re.compile('description|overview|summary', re.I)),
        soup.find('p', class_=re.compile('description|overview|summary', re.I)),
        soup.find('div', {'data-testid': re.compile('description', re.I)}),
    ]
    for selector in desc_selectors:
        if selector:
            details['description'] = selector.get_text(strip=True)
            break
    
    # Extract metadata (adaptive support, remote support, duration, test type)
    # Look for common patterns in the page
    text = soup.get_text()
    
    # Adaptive support
    if re.search(r'adaptive', text, re.I):
        details['adaptive_support'] = 'Yes' if re.search(r'adaptive.*yes|supports.*adaptive', text, re.I) else 'No'
    else:
        details['adaptive_support'] = 'No'
    
    # Remote support
    if re.search(r'remote|online', text, re.I):
        details['remote_support'] = 'Yes'
    else:
        details['remote_support'] = 'Yes'  # Default assumption
    
    # Duration (look for patterns like "30 minutes", "1 hour", etc.)
    duration_match = re.search(r'(\d+)\s*(?:min|minute|hour|hr)', text, re.I)
    if duration_match:
        num = int(duration_match.group(1))
        if 'hour' in duration_match.group(0).lower():
            details['duration'] = num * 60
        else:
            details['duration'] = num
    else:
        details['duration'] = 30  # Default
    
    # Test type (look for categories)
    test_types = []
    type_keywords = {
        'Ability & Aptitude': ['ability', 'aptitude', 'cognitive', 'reasoning'],
        'Knowledge & Skills': ['knowledge', 'skill', 'technical', 'competency'],
        'Personality & Behavior': ['personality', 'behavior', 'behaviour', 'trait'],
        'Competencies': ['competency', 'competence'],
        'Biodata & Situational Judgement': ['biodata', 'situational', 'judgement'],
    }
    
    for test_type, keywords in type_keywords.items():
        if any(kw in text.lower() for kw in keywords):
            test_types.append(test_type)
    
    if not test_types:
        test_types = ['Unknown']
    
    details['test_type'] = '|'.join(test_types)
    
    return details


def scrape_catalogue_page(page_url, seen_urls):
    """Scrape assessments from a catalogue page."""
    html = get_page_content(page_url)
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    assessments = []
    
    # Find all assessment links
    # Common patterns: links containing "product-catalog/view" or assessment names
    links = soup.find_all('a', href=True)
    
    for link in links:
        href = link.get('href', '')
        full_url = urljoin(BASE_URL, href)
        
        # Check if it's an assessment link (not pre-packaged)
        if 'product-catalog/view' in href or 'solutions/products' in href:
            # Skip pre-packaged solutions
            if 'pre-packaged' in href.lower() or 'prepackaged' in href.lower():
                continue
            
            # Skip if already seen
            if full_url in seen_urls:
                continue
            
            # Extract basic info from link
            name = link.get_text(strip=True)
            if not name or len(name) < 3:
                # Try to find name in parent elements
                parent = link.find_parent(['div', 'li', 'article'])
                if parent:
                    name_elem = parent.find(['h2', 'h3', 'h4', 'span', 'div'], class_=re.compile('title|name', re.I))
                    if name_elem:
                        name = name_elem.get_text(strip=True)
            
            if name and len(name) > 2:
                seen_urls.add(full_url)
                assessments.append({
                    'url': full_url,
                    'name': name,
                    'description': '',
                    'adaptive_support': 'No',
                    'remote_support': 'Yes',
                    'duration': 30,
                    'test_type': 'Unknown'
                })
    
    return assessments


def scrape_shl_catalogue():
    """Main function to scrape SHL Individual Test Solutions."""
    print("=" * 60)
    print("SHL Catalogue Scraper")
    print("=" * 60)
    print(f"\nTarget URL: {CATALOGUE_URL}")
    print("Filtering: Individual Test Solutions only (excluding Pre-packaged)")
    print("\nStarting scrape...\n")
    
    all_assessments = []
    seen_urls = set()
    
    # Start with the main catalogue page
    print("1. Scraping main catalogue page...")
    html = get_page_content(CATALOGUE_URL)
    
    if not html:
        print("ERROR: Could not fetch main catalogue page")
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Method 1: Look for assessment links directly on the page
    print("2. Extracting assessment links...")
    assessments = scrape_catalogue_page(CATALOGUE_URL, seen_urls)
    all_assessments.extend(assessments)
    print(f"   Found {len(assessments)} assessments so far...")
    
    # Method 2: Look for pagination or "Load More" buttons
    # Check for pagination links
    pagination_links = soup.find_all('a', href=re.compile(r'page|pagination|next', re.I))
    for link in pagination_links[:5]:  # Limit to first 5 pages
        page_url = urljoin(BASE_URL, link.get('href'))
        if page_url not in seen_urls:
            print(f"3. Scraping page: {page_url}")
            page_assessments = scrape_catalogue_page(page_url, seen_urls)
            all_assessments.extend(page_assessments)
            print(f"   Found {len(page_assessments)} more assessments...")
            time.sleep(2)  # Be respectful
    
    # Method 3: Try to find assessment cards/items
    print("4. Looking for assessment items in page structure...")
    # Common selectors for assessment items
    item_selectors = [
        soup.find_all('div', class_=re.compile('product|assessment|item|card', re.I)),
        soup.find_all('article', class_=re.compile('product|assessment', re.I)),
        soup.find_all('li', class_=re.compile('product|assessment', re.I)),
    ]
    
    for items in item_selectors:
        for item in items:
            # Look for links within items
            link = item.find('a', href=True)
            if link:
                href = link.get('href', '')
                if 'product-catalog' in href and 'pre-packaged' not in href.lower():
                    full_url = urljoin(BASE_URL, href)
                    if full_url not in seen_urls:
                        name = link.get_text(strip=True)
                        if not name:
                            name_elem = item.find(['h2', 'h3', 'h4', 'span'], class_=re.compile('title|name', re.I))
                            if name_elem:
                                name = name_elem.get_text(strip=True)
                        
                        if name and len(name) > 2:
                            seen_urls.add(full_url)
                            all_assessments.append({
                                'url': full_url,
                                'name': name,
                                'description': '',
                                'adaptive_support': 'No',
                                'remote_support': 'Yes',
                                'duration': 30,
                                'test_type': 'Unknown'
                            })
    
    # Remove duplicates based on URL
    unique_assessments = {}
    for assessment in all_assessments:
        url = assessment['url']
        if url not in unique_assessments:
            unique_assessments[url] = assessment
    
    all_assessments = list(unique_assessments.values())
    print(f"\n5. Found {len(all_assessments)} unique Individual Test Solutions")
    
    # Now extract detailed information from each assessment page
    print("\n6. Extracting detailed information from assessment pages...")
    print("   This may take a while...")
    
    detailed_assessments = []
    for i, assessment in enumerate(all_assessments, 1):
        print(f"   Processing {i}/{len(all_assessments)}: {assessment['name'][:50]}...")
        details = extract_assessment_details(assessment['url'])
        
        # Merge details
        assessment.update(details)
        detailed_assessments.append(assessment)
        
        # Be respectful - add delay
        if i % 10 == 0:
            time.sleep(1)
        else:
            time.sleep(0.5)
    
    # Create DataFrame
    df = pd.DataFrame(detailed_assessments)
    
    # Ensure required columns
    required_cols = ['url', 'name', 'description', 'adaptive_support', 'remote_support', 'duration', 'test_type']
    for col in required_cols:
        if col not in df.columns:
            df[col] = ''
    
    # Reorder columns
    df = df[required_cols]
    
    # Save to CSV
    output_path = Path("data/catalogue.csv")
    output_path.parent.mkdir(exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"\n{'='*60}")
    print("Scraping Complete!")
    print(f"{'='*60}")
    print(f"\nTotal assessments scraped: {len(df)}")
    print(f"Saved to: {output_path}")
    
    if len(df) < 377:
        print(f"\n⚠️  WARNING: Only {len(df)} assessments found.")
        print("   Requirement: At least 377 Individual Test Solutions")
        print("   You may need to:")
        print("   1. Check if the website structure has changed")
        print("   2. Look for additional pages or filters")
        print("   3. Manually verify the scraping logic")
    else:
        print(f"\n✅ Success! Scraped {len(df)} assessments (requirement: 377+)")
    
    return df


if __name__ == "__main__":
    df = scrape_shl_catalogue()
    if df is not None:
        print(f"\nFirst few assessments:")
        print(df.head())
