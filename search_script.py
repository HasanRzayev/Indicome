#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULTRA-ADVANCED SCRAPER - Maximum Anti-Block
"""

import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import logging
import random
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)

# Ultra-realistic User-Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:123.0) Gecko/20100101 Firefox/123.0',
]

def get_advanced_headers(referer=None):
    """Get ultra-realistic headers"""
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none' if not referer else 'same-origin',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
    }
    
    if referer:
        headers['Referer'] = referer
    
    return headers

def create_session():
    """Create session with retry strategy"""
    session = requests.Session()
    
    retry = Retry(
        total=3,
        read=3,
        connect=3,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 504, 429)
    )
    
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    return session

def make_advanced_request(url, referer=None):
    """Advanced HTTP request with anti-detection"""
    try:
        session = create_session()
        
        # Random delay to avoid rate limiting
        time.sleep(random.uniform(0.5, 1.5))
        
        response = session.get(
            url,
            headers=get_advanced_headers(referer),
            timeout=20,
            allow_redirects=True
        )
        
        if response.status_code == 200:
            return response
        
        logging.warning(f"Status code: {response.status_code}")
        return None
        
    except Exception as e:
        logging.error(f"Request failed: {e}")
        return None

def clean_price(text):
    """Extract clean price"""
    if not text:
        return "See price"
    
    text = text.replace(',', '').replace('$', '').strip()
    price_match = re.search(r'(\d+\.?\d*)', text)
    
    if price_match:
        return f"${price_match.group(1)}"
    
    return "See price"

def clean_title(text):
    """Clean and normalize title"""
    if not text:
        return ""
    
    text = ' '.join(text.split())
    text = text.replace('\n', ' ').replace('\r', '')
    
    return text[:200]

# ============================================================================
# EBAY - ULTRA ADVANCED
# ============================================================================

def fetch_ebay(query):
    """eBay scraper - ultra advanced version"""
    try:
        url = f"https://www.ebay.com/sch/i.html?_nkw={urllib.parse.quote(query)}&_sacat=0&LH_TitleDesc=0&_sop=12"
        logging.info(f"[eBay] Fetching: {query}")
        
        response = make_advanced_request(url)
        if not response:
            logging.error("[eBay] Failed to fetch")
            return []
        
        soup = BeautifulSoup(response.text, 'lxml')
        results = []
        
        # Multiple strategies
        items = (soup.select('li.s-item.s-item__pl-on-bottom') or 
                soup.select('li.s-item') or 
                soup.select('div.s-item__wrapper'))
        
        logging.info(f"[eBay] Found {len(items)} potential items")
        
        for item in items[:20]:
            try:
                # Title - multiple selectors
                title = None
                for selector in ['.s-item__title', 'h3.s-item__title', '.s-item__title span', 'h3']:
                    elem = item.select_one(selector)
                    if elem:
                        title = clean_title(elem.get_text())
                        break
                
                if not title:
                    continue
                
                # Skip ads
                skip_words = ['shop on ebay', 'sponsored', 'see all', 'new listing', 'shop ebay']
                if any(word in title.lower() for word in skip_words):
                    continue
                
                if len(title) < 10:
                    continue
                
                # Link
                link = None
                for selector in ['a.s-item__link', 'a[href*="/itm/"]', 'a']:
                    elem = item.select_one(selector)
                    if elem and elem.get('href'):
                        href = elem['href']
                        if '/itm/' in href or '/p/' in href:
                            link = href.split('?')[0]
                            break
                
                if not link or 'javascript' in link:
                    continue
                
                # Price
                price = "See price"
                for selector in ['.s-item__price', 'span.s-item__price', '.s-item__price span']:
                    elem = item.select_one(selector)
                    if elem:
                        price = clean_price(elem.get_text())
                        break
                
                results.append({
                    "site": "eBay",
                    "title": title,
                    "link": link,
                    "price": price
                })
                
                if len(results) >= 3:
                    break
                    
            except Exception as e:
                logging.debug(f"[eBay] Item error: {e}")
                continue
        
        logging.info(f"[eBay] Returning {len(results)} results")
        return results
        
    except Exception as e:
        logging.error(f"[eBay] Error: {e}")
        return []

# ============================================================================
# WALMART - ULTRA ADVANCED
# ============================================================================

def fetch_walmart(query):
    """Walmart scraper - ultra advanced version"""
    try:
        url = f"https://www.walmart.com/search?q={urllib.parse.quote(query)}"
        logging.info(f"[Walmart] Fetching: {query}")
        
        response = make_advanced_request(url, referer='https://www.walmart.com')
        if not response:
            logging.error("[Walmart] Failed to fetch")
            return []
        
        soup = BeautifulSoup(response.text, 'lxml')
        results = []
        
        # Find all potential product links
        all_links = soup.find_all('a', href=True)
        product_links = [a for a in all_links if '/ip/' in a.get('href', '')]
        
        logging.info(f"[Walmart] Found {len(product_links)} product links")
        
        seen_urls = set()
        
        for link in product_links[:30]:
            try:
                href = link['href']
                
                if href in seen_urls:
                    continue
                
                # Get title from multiple sources
                title = (link.get('aria-label') or 
                        link.get('title') or 
                        link.get_text(strip=True))
                
                title = clean_title(title)
                
                if not title or len(title) < 15:
                    continue
                
                # Skip if it's not a real product title
                if any(skip in title.lower() for skip in ['walmart', 'search', 'shop', 'all departments']):
                    continue
                
                # Build URL
                if href.startswith('/'):
                    href = 'https://www.walmart.com' + href
                
                # Clean URL
                href = href.split('?')[0]
                
                if href in seen_urls:
                    continue
                
                seen_urls.add(href)
                
                # Try to find price nearby
                price = "See price"
                parent = link.find_parent(['div', 'article', 'section'])
                if parent:
                    # Multiple price selectors
                    for selector in ['[data-automation-id*="price"]', 'span[class*="price"]', 'div[class*="price"]']:
                        price_elem = parent.select_one(selector)
                        if price_elem:
                            price_text = price_elem.get_text()
                            if '$' in price_text or any(c.isdigit() for c in price_text):
                                price = clean_price(price_text)
                                break
                
                results.append({
                    "site": "Walmart",
                    "title": title,
                    "link": href,
                    "price": price
                })
                
                if len(results) >= 3:
                    break
                    
            except Exception as e:
                logging.debug(f"[Walmart] Item error: {e}")
                continue
        
        logging.info(f"[Walmart] Returning {len(results)} results")
        return results
        
    except Exception as e:
        logging.error(f"[Walmart] Error: {e}")
        return []

# ============================================================================
# AMAZON - OPTIMIZED
# ============================================================================

def fetch_amazon(query):
    """Amazon scraper - optimized version"""
    try:
        url = f"https://www.amazon.com/s?k={urllib.parse.quote(query)}&ref=nb_sb_noss"
        logging.info(f"[Amazon] Fetching: {query}")
        
        response = make_advanced_request(url, referer='https://www.amazon.com')
        if not response:
            logging.error("[Amazon] Failed to fetch")
            return []
        
        soup = BeautifulSoup(response.text, 'lxml')
        results = []
        
        # Find products with ASIN
        products = soup.select('[data-asin]:not([data-asin=""])')
        
        logging.info(f"[Amazon] Found {len(products)} products")
        
        for product in products[:20]:
            try:
                asin = product.get('data-asin')
                
                if not asin or len(asin) != 10:
                    continue
                
                # Title
                title = None
                for selector in ['h2 a span', 'h2 span', '.a-text-normal', 'h2']:
                    elem = product.select_one(selector)
                    if elem:
                        title = clean_title(elem.get_text())
                        if len(title) > 15:
                            break
                
                if not title or len(title) < 15:
                    continue
                
                # Build clean Amazon link
                link = f"https://www.amazon.com/dp/{asin}"
                
                # Price
                price = "See price"
                for selector in ['.a-price-whole', '.a-price .a-offscreen', 'span.a-price']:
                    elem = product.select_one(selector)
                    if elem:
                        price = clean_price(elem.get_text())
                        if price != "See price":
                            break
                
                results.append({
                    "site": "Amazon",
                    "title": title,
                    "link": link,
                    "price": price
                })
                
                if len(results) >= 3:
                    break
                    
            except Exception as e:
                logging.debug(f"[Amazon] Item error: {e}")
                continue
        
        logging.info(f"[Amazon] Returning {len(results)} results")
        return results
        
    except Exception as e:
        logging.error(f"[Amazon] Error: {e}")
        return []

# ============================================================================
# OTHER SITES
# ============================================================================

def fetch_trendyol(query):
    logging.info(f"[Trendyol] Skipped")
    return []

def fetch_aliexpress(query):
    logging.info(f"[AliExpress] Skipped")
    return []

def fetch_target(query):
    logging.info(f"[Target] Skipped")
    return []
