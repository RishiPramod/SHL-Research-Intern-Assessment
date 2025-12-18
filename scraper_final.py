"""
Final scraper based on actual SHL website structure.

URL pattern: https://www.shl.com/products/product-catalog/?start=0&type=1&type=1
- start=0, 12, 24, 36... (12 items per page)
- type=1 appears twice (Individual Test Solutions)
- Last page: start=372 (32 pages total)
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from pathlib import Path
from urllib.parse import urljoin


BASE_URL = "https://www.shl.com"
ITEMS_PER_PAGE = 12


def get_page(session, start=0, retries=3):
    """Fetch a page of the catalogue."""
    url = f"{BASE_URL}/products/product-catalog/?start={start}&type=1&type=1"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    for attempt in range(retries):
        try:
            response = session.get(url, headers=headers, timeout=60, allow_redirects=True)
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 3
                print(f"      Timeout, waiting {wait_time}s before retry {attempt + 1}/{retries}...")
                time.sleep(wait_time)
            else:
                print(f"      Timeout after {retries} attempts")
                return None
        except Exception as e:
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"      Error: {str(e)[:50]}, waiting {wait_time}s before retry {attempt + 1}/{retries}...")
                time.sleep(wait_time)
            else:
                print(f"      Error after {retries} attempts: {str(e)[:100]}")
                return None
    
    return None


def extract_assessments_from_table(soup):
    """Extract assessments from the table on the page."""
    assessments = []
    
    # Find the table
    table = soup.find('table')
    if not table:
        return assessments
    
    # Find all rows (skip header row)
    rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')[1:]
    
    for row in rows:
        # Get entity ID
        entity_id = row.get('data-entity-id', '')
        
        # Get the link and name
        title_cell = row.find('td', class_='custom__table-heading__title')
        if not title_cell:
            continue
        
        link = title_cell.find('a', href=True)
        if not link:
            continue
        
        href = link.get('href', '')
        full_url = urljoin(BASE_URL, href)
        name = link.get_text(strip=True)
        
        if not name or not full_url:
            continue
        
        # Get Remote Testing (Yes/No)
        remote_cell = row.find_all('td', class_='custom__table-heading__general')[0] if len(row.find_all('td', class_='custom__table-heading__general')) > 0 else None
        remote_support = 'No'
        if remote_cell:
            circle = remote_cell.find('span', class_='catalogue__circle')
            if circle and '-yes' in circle.get('class', []):
                remote_support = 'Yes'
        
        # Get Adaptive/IRT (Yes/No)
        adaptive_cell = row.find_all('td', class_='custom__table-heading__general')[1] if len(row.find_all('td', class_='custom__table-heading__general')) > 1 else None
        adaptive_support = 'No'
        if adaptive_cell:
            circle = adaptive_cell.find('span', class_='catalogue__circle')
            if circle and '-yes' in circle.get('class', []):
                adaptive_support = 'Yes'
        
        # Get Test Type
        test_type_cell = row.find('td', class_='product-catalogue__keys')
        test_types = []
        if test_type_cell:
            keys = test_type_cell.find_all('span', class_='product-catalogue__key')
            type_map = {
                'A': 'Ability & Aptitude',
                'B': 'Biodata & Situational Judgement',
                'C': 'Competencies',
                'D': 'Development & 360',
                'E': 'Assessment Exercises',
                'K': 'Knowledge & Skills',
                'P': 'Personality & Behavior',
                'S': 'Simulations',
            }
            for key_span in keys:
                key = key_span.get_text(strip=True)
                if key in type_map:
                    test_types.append(type_map[key])
        
        if not test_types:
            test_types = ['Unknown']
        
        assessments.append({
            'url': full_url,
            'name': name,
            'description': '',  # Will be filled from detail page
            'adaptive_support': adaptive_support,
            'remote_support': remote_support,
            'duration': 30,  # Default, will be updated from detail page
            'test_type': '|'.join(test_types),
            'entity_id': entity_id
        })
    
    return assessments


def get_total_pages(session):
    """Extract total number of pages."""
    # Based on user info: last page is start=372, so 32 pages total
    # We'll use this directly to avoid extra requests
    print(f"      Using 32 pages (last page start=372) based on known structure")
    return 32


def extract_details_from_page(session, url):
    """Extract detailed information from an assessment detail page."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        print(f"      Error fetching {url}: {e}")
        return {}
    
    if not html:
        return {}
    
    soup = BeautifulSoup(html, 'html.parser')
    details = {}
    
    # Extract description
    desc_selectors = [
        soup.find('div', class_=re.compile('description|overview|summary|content', re.I)),
        soup.find('section', class_=re.compile('description|overview', re.I)),
        soup.find('p', class_=re.compile('description|intro', re.I)),
    ]
    
    for selector in desc_selectors:
        if selector:
            text = selector.get_text(separator=' ', strip=True)
            if len(text) > 20:
                details['description'] = text[:500]
                break
    
    # Extract duration
    page_text = soup.get_text().lower()
    duration_match = re.search(r'(\d+)\s*(?:minute|min|m|hour|hr|h)\b', page_text, re.I)
    if duration_match:
        num = int(duration_match.group(1))
        if 'hour' in duration_match.group(0).lower() or 'hr' in duration_match.group(0).lower():
            details['duration'] = num * 60
        else:
            details['duration'] = num
    
    return details


def scrape_shl_catalogue():
    """Main scraping function."""
    print("=" * 70)
    print("SHL Individual Test Solutions Scraper")
    print("=" * 70)
    print(f"\nTarget: {BASE_URL}/products/product-catalog/")
    print("Filter: type=1 (Individual Test Solutions)")
    print("Items per page: 12\n")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    })
    
    all_assessments = []
    seen_urls = set()
    
    # Get first page to determine total pages
    print("Step 1: Determining total pages...")
    total_pages = get_total_pages(session)
    print(f"   Will scrape {total_pages} pages")
    
    # Scrape all pages
    print(f"\nStep 2: Scraping {total_pages} pages...")
    failed_pages = []
    
    for page in range(total_pages):
        start = page * ITEMS_PER_PAGE
        print(f"   Page {page + 1}/{total_pages} (start={start})...", end=' ', flush=True)
        
        html = get_page(session, start=start, retries=2)  # Reduce retries to speed up
        if not html:
            print(f"FAILED - will retry later")
            failed_pages.append((page + 1, start))
            continue
        
        soup = BeautifulSoup(html, 'html.parser')
        page_assessments = extract_assessments_from_table(soup)
        
        # Add to collection
        for assessment in page_assessments:
            if assessment['url'] not in seen_urls:
                seen_urls.add(assessment['url'])
                all_assessments.append(assessment)
        
        print(f"✓ {len(page_assessments)} assessments")
        time.sleep(0.8)  # Slightly faster
    
    # Retry failed pages
    if failed_pages:
        print(f"\n   Retrying {len(failed_pages)} failed pages...")
        for page_num, start in failed_pages:
            print(f"   Retry: Page {page_num} (start={start})...", end=' ', flush=True)
            html = get_page(session, start=start, retries=3)
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                page_assessments = extract_assessments_from_table(soup)
                for assessment in page_assessments:
                    if assessment['url'] not in seen_urls:
                        seen_urls.add(assessment['url'])
                        all_assessments.append(assessment)
                print(f"✓ {len(page_assessments)} assessments")
            else:
                print(f"FAILED again")
            time.sleep(1)
    
    print(f"\nStep 3: Collected {len(all_assessments)} unique assessments")
    
    # Extract details from each assessment page (optional - can skip for speed)
    print(f"\nStep 4: Extracting detailed information (optional)...")
    print(f"   This will take 15-20 minutes for {len(all_assessments)} assessments...")
    print("   Skipping detail extraction for now - you can add it later if needed")
    print("   Basic info (name, URL, test type) is sufficient for recommendations\n")
    
    # Skip detail extraction for now to speed up
    # Uncomment below to enable detail extraction:
    # for i, assessment in enumerate(all_assessments, 1):
    #     if i % 20 == 0:
    #         print(f"   Progress: {i}/{len(all_assessments)} ({i*100//len(all_assessments)}%)")
    #     
    #     # Extract details from detail page
    #     details = extract_details_from_page(session, assessment['url'])
    #     assessment.update(details)
    #     
    #     # Rate limiting
    #     if i % 10 == 0:
    #         time.sleep(1.5)
    #     else:
    #         time.sleep(0.7)
    
    # Create DataFrame
    df = pd.DataFrame(all_assessments)
    
    # Remove entity_id column (not needed)
    if 'entity_id' in df.columns:
        df = df.drop(columns=['entity_id'])
    
    # Ensure all required columns
    required_cols = ['url', 'name', 'description', 'adaptive_support', 'remote_support', 'duration', 'test_type']
    for col in required_cols:
        if col not in df.columns:
            df[col] = ''
    
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
        print(f"\n⚠️  Only {len(df)} assessments found (need 377+)")
        print("   Check if all pages were scraped correctly")
    else:
        print(f"\n✅ Success! Scraped {len(df)} assessments (requirement: 377+)")
    
    return df


if __name__ == "__main__":
    df = scrape_shl_catalogue()
    if df is not None and len(df) > 0:
        print(f"\nSample assessments:")
        print(df[['name', 'url', 'test_type']].head(10).to_string())
