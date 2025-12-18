"""
Selenium-based scraper for SHL website (handles JavaScript-rendered content).

This requires: pip install selenium webdriver-manager
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import re
from pathlib import Path
from bs4 import BeautifulSoup


BASE_URL = "https://www.shl.com"
CATALOGUE_URL = "https://www.shl.com/solutions/products/product-catalog/"


def setup_driver():
    """Setup Chrome driver with options."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def scrape_with_selenium():
    """Scrape using Selenium to handle JavaScript."""
    print("=" * 70)
    print("SHL Catalogue Scraper (Selenium - JavaScript Support)")
    print("=" * 70)
    print("\n⚠️  Note: This requires Chrome browser and ChromeDriver")
    print("   Install: pip install selenium webdriver-manager\n")
    
    try:
        driver = setup_driver()
    except Exception as e:
        print(f"ERROR: Could not setup Selenium driver: {e}")
        print("\nPlease install:")
        print("  pip install selenium webdriver-manager")
        return None
    
    all_assessments = []
    seen_urls = set()
    
    try:
        print(f"Step 1: Loading {CATALOGUE_URL}...")
        driver.get(CATALOGUE_URL)
        time.sleep(5)  # Wait for JavaScript to load
        
        # Wait for page to load
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except:
            print("   Warning: Page may not have loaded completely")
        
        print("   ✓ Page loaded")
        
        # Get page source after JavaScript execution
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for filters - need to filter for Individual Test Solutions
        print("\nStep 2: Looking for filter options...")
        
        # Try to find and click filter for "Individual Test Solutions"
        filter_selectors = [
            "//button[contains(text(), 'Individual')]",
            "//a[contains(text(), 'Individual')]",
            "//label[contains(text(), 'Individual')]",
            "//input[@value='Individual']",
        ]
        
        filter_clicked = False
        for selector in filter_selectors:
            try:
                element = driver.find_element(By.XPATH, selector)
                driver.execute_script("arguments[0].click();", element)
                time.sleep(3)
                filter_clicked = True
                print("   ✓ Applied Individual Test Solutions filter")
                break
            except:
                continue
        
        if not filter_clicked:
            print("   ⚠️  Could not find filter - will scrape all and filter later")
        
        # Look for "Load More" or pagination
        print("\nStep 3: Loading all assessments...")
        
        # Scroll to load more content (lazy loading)
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scrolls = 20
        
        while scroll_attempts < max_scrolls:
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Check for "Load More" button
            try:
                load_more = driver.find_element(By.XPATH, "//button[contains(text(), 'Load More')] | //a[contains(text(), 'Load More')] | //button[contains(text(), 'Show More')]")
                driver.execute_script("arguments[0].click();", load_more)
                time.sleep(3)
            except:
                pass
            
            # Check if new content loaded
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempts += 1
        
        print(f"   Scrolled {scroll_attempts} times to load content")
        
        # Get final page source
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract all assessment links
        print("\nStep 4: Extracting assessment links...")
        
        # Find all links
        links = soup.find_all('a', href=True)
        assessment_links = []
        
        for link in links:
            href = link.get('href', '')
            full_url = href if href.startswith('http') else f"{BASE_URL}{href}"
            
            # Check if it's an assessment link
            if ('product-catalog' in href or 'solutions/products' in href) and 'view' in href:
                # Skip pre-packaged
                if 'pre-packaged' in href.lower() or 'prepackaged' in href.lower():
                    continue
                
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    name = link.get_text(strip=True)
                    if not name or len(name) < 3:
                        parent = link.find_parent(['div', 'li', 'article'])
                        if parent:
                            name_elem = parent.find(['h2', 'h3', 'h4', 'span', 'div'], 
                                                   class_=re.compile('title|name', re.I))
                            if name_elem:
                                name = name_elem.get_text(strip=True)
                    
                    if name and len(name) > 2:
                        assessment_links.append((full_url, name))
        
        print(f"   Found {len(assessment_links)} assessment links")
        
        # Also try to find assessment cards/items
        items = soup.find_all(['div', 'article', 'li'], 
                            class_=re.compile('product|assessment|item|card', re.I))
        
        for item in items:
            link = item.find('a', href=True)
            if link:
                href = link.get('href', '')
                if 'product-catalog' in href and 'view' in href and 'pre-packaged' not in href.lower():
                    full_url = href if href.startswith('http') else f"{BASE_URL}{href}"
                    if full_url not in seen_urls:
                        seen_urls.add(full_url)
                        name = link.get_text(strip=True)
                        if not name:
                            name_elem = item.find(['h2', 'h3', 'h4'])
                            if name_elem:
                                name = name_elem.get_text(strip=True)
                        if name and len(name) > 2:
                            assessment_links.append((full_url, name))
        
        # Remove duplicates
        unique_links = {}
        for url, name in assessment_links:
            if url not in unique_links:
                unique_links[url] = name
        
        assessment_links = list(unique_links.items())
        print(f"   Total unique assessments: {len(assessment_links)}")
        
        # Extract details from each assessment
        print(f"\nStep 5: Extracting details from {len(assessment_links)} assessments...")
        print("   This will take several minutes...\n")
        
        for i, (url, name) in enumerate(assessment_links, 1):
            print(f"   [{i}/{len(assessment_links)}] {name[:60]}...")
            
            assessment = {
                'url': url,
                'name': name,
                'description': '',
                'adaptive_support': 'No',
                'remote_support': 'Yes',
                'duration': 30,
                'test_type': 'Unknown'
            }
            
            # Visit assessment page
            try:
                driver.get(url)
                time.sleep(2)
                
                page_html = driver.page_source
                page_soup = BeautifulSoup(page_html, 'html.parser')
                
                # Extract details
                # Name
                h1 = page_soup.find('h1')
                if h1:
                    assessment['name'] = h1.get_text(strip=True)
                
                # Description
                desc = page_soup.find('div', class_=re.compile('description|overview|summary', re.I))
                if desc:
                    assessment['description'] = desc.get_text(separator=' ', strip=True)[:500]
                
                # Metadata
                text = page_soup.get_text().lower()
                
                if re.search(r'\badaptive\b', text):
                    assessment['adaptive_support'] = 'Yes'
                
                # Duration
                dur_match = re.search(r'(\d+)\s*(?:min|minute|hour|hr)', text, re.I)
                if dur_match:
                    num = int(dur_match.group(1))
                    assessment['duration'] = num * 60 if 'hour' in dur_match.group(0).lower() else num
                
                # Test type
                types = []
                if re.search(r'\b(ability|aptitude|cognitive|reasoning)\b', text):
                    types.append('Ability & Aptitude')
                if re.search(r'\b(knowledge|skill|technical|competency)\b', text):
                    types.append('Knowledge & Skills')
                if re.search(r'\b(personality|behavior|behaviour|trait)\b', text):
                    types.append('Personality & Behavior')
                
                assessment['test_type'] = '|'.join(types) if types else 'Unknown'
                
            except Exception as e:
                print(f"      Error extracting details: {e}")
            
            all_assessments.append(assessment)
            
            if i % 10 == 0:
                time.sleep(1)
        
    finally:
        driver.quit()
    
    # Create DataFrame and save
    df = pd.DataFrame(all_assessments)
    
    required_cols = ['url', 'name', 'description', 'adaptive_support', 'remote_support', 'duration', 'test_type']
    for col in required_cols:
        if col not in df.columns:
            df[col] = ''
    
    df = df[required_cols]
    df = df.drop_duplicates(subset=['url'])
    
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
    else:
        print(f"\n✅ Success! Scraped {len(df)} assessments")
    
    return df


if __name__ == "__main__":
    try:
        df = scrape_with_selenium()
        if df is not None and len(df) > 0:
            print(f"\nSample:")
            print(df[['name', 'url']].head(10))
    except ImportError:
        print("\nERROR: Selenium not installed")
        print("Install with: pip install selenium webdriver-manager")
