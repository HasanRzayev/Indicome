#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROFESSIONAL SCRAPER - Anti-Block, Real Data
"""

import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import logging
import random
import time

logging.basicConfig(level=logging.INFO)

# Rotating User-Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
]

def get_headers():
    """Get random headers to avoid blocking"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }

def make_request(url, max_retries=3):
    """Make HTTP request with retry logic"""
    for attempt in range(max_retries):
        try:
            session = requests.Session()
            response = session.get(url, headers=get_headers(), timeout=15, allow_redirects=True)
            
            if response.status_code == 200:
                return response
            
            time.sleep(1)  # Wait before retry
        except Exception as e:
            logging.warning(f"Request attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    return None

def clean_price(text):
    """Extract clean price from text"""
    if not text:
        return "See price"
    
    # Remove currency symbols and extract numbers
    price_match = re.search(r'[\$£€₺]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
    if price_match:
        price = price_match.group(1).replace(',', '')
        return f"${price}"
    
    return "See price"

def clean_title(text):
    """Clean product title"""
    if not text:
        return ""
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text[:150]  # Limit length

# ============================================================================
# EBAY SCRAPER
# ============================================================================

def fetch_ebay(query):
    """eBay scraper with anti-block measures"""
    try:
        url = f"https://www.ebay.com/sch/i.html?_nkw={urllib.parse.quote(query)}&_sacat=0"
        logging.info(f"[eBay] Fetching: {query}")
        
        response = make_request(url)
        if not response:
            logging.error("[eBay] Failed to fetch")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Try multiple selectors
        items = soup.select('li.s-item') or soup.select('div.s-item')
        
        for item in items[:15]:
            try:
                # Title - multiple attempts
                title_elem = (item.select_one('.s-item__title') or 
                             item.select_one('h3.s-item__title') or
                             item.select_one('[class*="item__title"]'))
                
                if not title_elem:
                    continue
                
                title = clean_title(title_elem.get_text())
                
                # Skip ads
                if any(skip in title.lower() for skip in ['shop on ebay', 'sponsored', 'advertisement']):
                    continue
                
                # Link
                link_elem = item.select_one('a.s-item__link') or item.select_one('a[href*="/itm/"]')
                if not link_elem or not link_elem.get('href'):
                    continue
                
                link = link_elem['href'].split('?')[0]  # Clean URL
                
                # Price
                price_elem = (item.select_one('.s-item__price') or 
                             item.select_one('[class*="item__price"]'))
                price = clean_price(price_elem.get_text() if price_elem else "")
                
                results.append({
                    "site": "eBay",
                    "title": title,
                    "link": link,
                    "price": price
                })
                
                if len(results) >= 3:
                    break
                    
            except Exception as e:
                logging.debug(f"[eBay] Item parse error: {e}")
                continue
        
        logging.info(f"[eBay] Found {len(results)} results")
        return results
        
    except Exception as e:
        logging.error(f"[eBay] Error: {e}")
        return []

# ============================================================================
# WALMART SCRAPER
# ============================================================================

def fetch_walmart(query):
    """Walmart scraper with anti-block"""
    try:
        url = f"https://www.walmart.com/search?q={urllib.parse.quote(query)}"
        logging.info(f"[Walmart] Fetching: {query}")
        
        response = make_request(url)
        if not response:
            logging.error("[Walmart] Failed to fetch")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Find product links
        product_links = soup.find_all('a', href=re.compile(r'/ip/\d+'))
        
        seen_urls = set()
        for link in product_links[:20]:
            try:
                href = link.get('href', '')
                if not href or href in seen_urls:
                    continue
                
                seen_urls.add(href)
                
                # Get title from various sources
                title = (link.get('aria-label') or 
                        link.get('title') or 
                        link.get_text(strip=True))
                
                title = clean_title(title)
                
                if not title or len(title) < 10:
                    continue
                
                # Build clean URL
                if href.startswith('/'):
                    href = 'https://www.walmart.com' + href
                
                # Clean URL from tracking
                href = href.split('?')[0]
                
                # Try to find price
                price = "See price"
                parent = link.find_parent('div')
                if parent:
                    price_elem = parent.find('span', attrs={'data-automation-id': 'product-price'})
                    if not price_elem:
                        price_elem = parent.find('span', text=re.compile(r'\$\d+'))
                    
                    if price_elem:
                        price = clean_price(price_elem.get_text())
                
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
        
        logging.info(f"[Walmart] Found {len(results)} results")
        return results
        
    except Exception as e:
        logging.error(f"[Walmart] Error: {e}")
        return []

# ============================================================================
# AMAZON SCRAPER
# ============================================================================

def fetch_amazon(query):
    """Amazon scraper with anti-block"""
    try:
        url = f"https://www.amazon.com/s?k={urllib.parse.quote(query)}"
        logging.info(f"[Amazon] Fetching: {query}")
        
        response = make_request(url)
        if not response:
            logging.error("[Amazon] Failed to fetch")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Multiple selector strategies
        products = (soup.select('[data-component-type="s-search-result"]') or
                   soup.select('div.s-result-item') or
                   soup.select('[data-asin]'))
        
        for product in products[:15]:
            try:
                # Get ASIN (unique ID)
                asin = product.get('data-asin')
                if not asin or len(asin) != 10:
                    continue
                
                # Title
                title_elem = (product.select_one('h2 a span') or 
                             product.select_one('h2 span') or
                             product.select_one('[class*="product-title"]'))
                
                if not title_elem:
                    continue
                
                title = clean_title(title_elem.get_text())
                
                if not title or len(title) < 10:
                    continue
                
                # Build clean link
                link = f"https://www.amazon.com/dp/{asin}"
                
                # Price
                price = "See price"
                price_elem = (product.select_one('.a-price-whole') or
                             product.select_one('.a-price') or
                             product.select_one('[class*="price"]'))
                
                if price_elem:
                    price_text = price_elem.get_text()
                    price = clean_price(price_text)
                
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
        
        logging.info(f"[Amazon] Found {len(results)} results")
        return results
        
    except Exception as e:
        logging.error(f"[Amazon] Error: {e}")
        return []

# ============================================================================
# OTHER SITES
# ============================================================================

def fetch_trendyol(query):
    """Trendyol - requires JavaScript rendering"""
    logging.info(f"[Trendyol] Skipped (JS required)")
    return []

def fetch_aliexpress(query):
    """AliExpress - requires JavaScript rendering"""
    logging.info(f"[AliExpress] Skipped (JS required)")
    return []

def fetch_target(query):
    """Target - requires JavaScript rendering"""
    logging.info(f"[Target] Skipped (JS required)")
    return []
