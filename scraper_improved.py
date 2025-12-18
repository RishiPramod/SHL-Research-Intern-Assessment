"""
Improved Selenium scraper with better filter detection and content loading.
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import re
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import json


BASE_URL = "https://www.shl.com"
CATALOGUE_URL = "https://www.shl.com/solutions/products/product-catalog/"


def setup_driver(headless=False):
    """Setup Chrome driver."""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def wait_for_element(driver, by, value, timeout=10):
    """Wait for element to be present."""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    except:
        return None


def find_and_click_filter(driver):
    """Find and click filter for Individual Test Solutions."""
    print("   Looking for filter options...")
    
    # Strategy 1: Look for filter buttons/links
    filter_selectors = [
        (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'individual')]"),
        (By.XPATH, "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'individual')]"),
        (By.XPATH, "//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'individual')]"),
        (By.XPATH, "//input[@type='checkbox' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'individual')]"),
        (By.XPATH, "//*[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'individual')]"),
        (By.CSS_SELECTOR, "[data-filter*='individual'], [data-category*='individual']"),
    ]
    
    for by, selector in filter_selectors:
        try:
            elements = driver.find_elements(by, selector)
            for elem in elements:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", elem)
                    time.sleep(2)
                    print(f"   ✓ Clicked filter: {elem.text[:50]}")
                    return True
                except:
                    continue
        except:
            continue
    
    # Strategy 2: Look for dropdowns or select elements
    try:
        selects = driver.find_elements(By.TAG_NAME, "select")
        for select in selects:
            options = select.find_elements(By.TAG_NAME, "option")
            for option in options:
                if 'individual' in option.text.lower() and 'pre-packaged' not in option.text.lower():
                    select.click()
                    time.sleep(0.5)
                    option.click()
                    time.sleep(2)
                    print(f"   ✓ Selected filter: {option.text}")
                    return True
    except:
        pass
    
    # Strategy 3: Look for tabs or category buttons
    try:
        tabs = driver.find_elements(By.XPATH, "//*[contains(@class, 'tab') or contains(@role, 'tab')]")
        for tab in tabs:
            if 'individual' in tab.text.lower():
                driver.execute_script("arguments[0].click();", tab)
                time.sleep(2)
                print(f"   ✓ Clicked tab: {tab.text[:50]}")
                return True
    except:
        pass
    
    print("   ⚠️  Could not find Individual Test Solutions filter")
    return False


def load_all_content(driver):
    """Scroll and load all content."""
    print("   Loading all content...")
    
    # Get initial page height
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    max_scrolls = 50
    no_change_count = 0
    
    while scroll_attempts < max_scrolls:
        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Try to find and click "Load More" or "Show More" buttons
        load_more_selectors = [
            (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]"),
            (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more')]"),
            (By.XPATH, "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]"),
            (By.CSS_SELECTOR, "[class*='load-more'], [class*='show-more'], [data-action*='load']"),
        ]
        
        for by, selector in load_more_selectors:
            try:
                button = driver.find_element(by, selector)
                if button.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(3)
                    print(f"      Clicked 'Load More' button")
                    break
            except:
                continue
        
        # Check if new content loaded
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            no_change_count += 1
            if no_change_count >= 3:
                break
        else:
            no_change_count = 0
            last_height = new_height
        
        scroll_attempts += 1
    
    print(f"   Scrolled {scroll_attempts} times, final height: {last_height}")
    return scroll_attempts


def extract_assessments_from_page(driver):
    """Extract all assessment links from current page."""
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    assessments = []
    seen_urls = set()
    
    # Method 1: Find all links with product-catalog/view
    links = soup.find_all('a', href=True)
    for link in links:
        href = link.get('href', '')
        if not href:
            continue
        
        # Build full URL
        if href.startswith('http'):
            full_url = href
        elif href.startswith('/'):
            full_url = BASE_URL + href
        else:
            full_url = urljoin(BASE_URL, href)
        
        # Check if it's an assessment link
        if ('product-catalog' in href or 'solutions/products' in href) and 'view' in href:
            # Skip pre-packaged
            if 'pre-packaged' in href.lower() or 'prepackaged' in href.lower():
                continue
            
            if full_url not in seen_urls:
                seen_urls.add(full_url)
                name = link.get_text(strip=True)
                
                # Try to get name from parent elements
                if not name or len(name) < 3:
                    parent = link.find_parent(['div', 'li', 'article', 'section', 'h2', 'h3', 'h4'])
                    if parent:
                        name_elem = parent.find(['h2', 'h3', 'h4', 'span', 'div'], 
                                               class_=re.compile('title|name|heading', re.I))
                        if name_elem:
                            name = name_elem.get_text(strip=True)
                
                if name and len(name) > 2:
                    assessments.append((full_url, name))
    
    # Method 2: Look for assessment cards/items
    items = soup.find_all(['div', 'article', 'li'], 
                        class_=re.compile('product|assessment|item|card', re.I))
    
    for item in items:
        link = item.find('a', href=True)
        if link:
            href = link.get('href', '')
            if 'product-catalog' in href and 'view' in href and 'pre-packaged' not in href.lower():
                full_url = href if href.startswith('http') else urljoin(BASE_URL, href)
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    name = link.get_text(strip=True)
                    if not name:
                        name_elem = item.find(['h2', 'h3', 'h4'])
                        if name_elem:
                            name = name_elem.get_text(strip=True)
                    if name and len(name) > 2:
                        assessments.append((full_url, name))
    
    # Remove duplicates
    unique_assessments = {}
    for url, name in assessments:
        if url not in unique_assessments:
            unique_assessments[url] = name
    
    return list(unique_assessments.items())


def check_for_api_calls(driver):
    """Check browser network logs for API calls."""
    print("   Checking for API endpoints...")
    
    # Get performance logs (if enabled)
    try:
        logs = driver.get_log('performance')
        for log in logs:
            message = json.loads(log['message'])
            if message['message']['method'] == 'Network.responseReceived':
                url = message['message']['params']['response']['url']
                if 'api' in url.lower() or 'catalog' in url.lower() or 'product' in url.lower():
                    print(f"      Found potential API: {url[:100]}")
    except:
        pass


def scrape_with_improved_selenium(headless=True):
    """Improved scraping with better filter and content detection."""
    print("=" * 70)
    print("SHL Catalogue Scraper (Improved Selenium)")
    print("=" * 70)
    print(f"\nTarget: {CATALOGUE_URL}")
    print("Note: Running in {'headless' if headless else 'visible'} mode\n")
    
    try:
        driver = setup_driver(headless=headless)
    except Exception as e:
        print(f"ERROR: Could not setup Selenium: {e}")
        print("\nInstall with: pip install selenium webdriver-manager")
        return None
    
    all_assessments = []
    
    try:
        # Load main page
        print("Step 1: Loading catalogue page...")
        driver.get(CATALOGUE_URL)
        time.sleep(5)
        
        # Wait for page to load
        wait_for_element(driver, By.TAG_NAME, "body", timeout=20)
        print("   ✓ Page loaded")
        
        # Save page source for debugging
        with open("page_source_debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("   ✓ Saved page source to page_source_debug.html")
        
        # Try to find and click filter
        print("\nStep 2: Applying Individual Test Solutions filter...")
        filter_clicked = find_and_click_filter(driver)
        
        if not filter_clicked:
            print("   ⚠️  Proceeding without filter - will filter results later")
        
        # Check for API calls
        check_for_api_calls(driver)
        
        # Load all content
        print("\nStep 3: Loading all assessments...")
        scroll_count = load_all_content(driver)
        
        # Extract assessments
        print("\nStep 4: Extracting assessment links...")
        assessments = extract_assessments_from_page(driver)
        print(f"   Found {len(assessments)} assessment links")
        
        if len(assessments) < 50:
            print("\n   ⚠️  Warning: Only found {len(assessments)} assessments")
            print("   Possible issues:")
            print("   1. Content may be loaded via API (check page_source_debug.html)")
            print("   2. Filter may not have been applied correctly")
            print("   3. Website structure may have changed")
            print("\n   Try running with headless=False to see what's happening")
        
        # Extract details from each assessment
        print(f"\nStep 5: Extracting details from {len(assessments)} assessments...")
        
        for i, (url, name) in enumerate(assessments, 1):
            print(f"   [{i}/{len(assessments)}] {name[:60]}...")
            
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
                
                # Extract details (same as before)
                h1 = page_soup.find('h1')
                if h1:
                    assessment['name'] = h1.get_text(strip=True)
                
                desc = page_soup.find('div', class_=re.compile('description|overview|summary', re.I))
                if desc:
                    assessment['description'] = desc.get_text(separator=' ', strip=True)[:500]
                
                text = page_soup.get_text().lower()
                
                if re.search(r'\badaptive\b', text):
                    assessment['adaptive_support'] = 'Yes'
                
                dur_match = re.search(r'(\d+)\s*(?:min|minute|hour|hr)', text, re.I)
                if dur_match:
                    num = int(dur_match.group(1))
                    assessment['duration'] = num * 60 if 'hour' in dur_match.group(0).lower() else num
                
                types = []
                if re.search(r'\b(ability|aptitude|cognitive|reasoning)\b', text):
                    types.append('Ability & Aptitude')
                if re.search(r'\b(knowledge|skill|technical|competency)\b', text):
                    types.append('Knowledge & Skills')
                if re.search(r'\b(personality|behavior|behaviour|trait)\b', text):
                    types.append('Personality & Behavior')
                
                assessment['test_type'] = '|'.join(types) if types else 'Unknown'
                
            except Exception as e:
                print(f"      Error: {e}")
            
            all_assessments.append(assessment)
            
            if i % 10 == 0:
                time.sleep(1)
        
    finally:
        driver.quit()
    
    # Create DataFrame and save
    df = pd.DataFrame(all_assessments)
    
    # Filter out pre-packaged if not already filtered
    df = df[~df['url'].str.contains('pre-packaged|prepackaged', case=False, na=False)]
    
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
        print("\nNext steps:")
        print("1. Check page_source_debug.html to see page structure")
        print("2. Try running with headless=False to see what's happening")
        print("3. Check browser DevTools for API endpoints")
        print("4. Manually verify the website structure")
    else:
        print(f"\n✅ Success! Scraped {len(df)} assessments")
    
    return df


if __name__ == "__main__":
    import sys
    
    headless = '--visible' not in sys.argv
    
    try:
        df = scrape_with_improved_selenium(headless=headless)
        if df is not None and len(df) > 0:
            print(f"\nSample assessments:")
            print(df[['name', 'url']].head(10))
    except ImportError:
        print("\nERROR: Selenium not installed")
        print("Install with: pip install selenium webdriver-manager")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
