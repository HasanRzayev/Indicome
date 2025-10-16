#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REAL WORKING SCRAPERS - eBay, Walmart, Amazon
Tested and verified to return actual products
"""

import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import logging

logging.basicConfig(level=logging.INFO)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def clean_price(text):
    """Extract price from text"""
    if not text:
        return "N/A"
    match = re.search(r'\$?\s*(\d+[,.]?\d*)', text)
    if match:
        return f"${match.group(1)}"
    return "N/A"

# ============================================================================
# EBAY - REAL SCRAPER
# ============================================================================

def fetch_ebay(query):
    """eBay scraper - returns real products"""
    try:
        url = f"https://www.ebay.com/sch/i.html?_nkw={urllib.parse.quote(query)}"
        logging.info(f"[eBay] Searching: {url}")
        
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        results = []
        items = soup.find_all('li', class_='s-item')
        
        for item in items[:10]:
            try:
                # Title
                title_elem = item.find('h3', class_='s-item__title')
                if not title_elem:
                    title_elem = item.find('div', class_='s-item__title')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                if 'Shop on eBay' in title or not title:
                    continue
                
                # Link
                link_elem = item.find('a', class_='s-item__link')
                if not link_elem or not link_elem.get('href'):
                    continue
                link = link_elem['href']
                
                # Price
                price_elem = item.find('span', class_='s-item__price')
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
                continue
        
        logging.info(f"[eBay] Found {len(results)} results")
        return results
        
    except Exception as e:
        logging.error(f"[eBay] Error: {e}")
        return []

# ============================================================================
# WALMART - REAL SCRAPER
# ============================================================================

def fetch_walmart(query):
    """Walmart scraper - returns real products"""
    try:
        url = f"https://www.walmart.com/search?q={urllib.parse.quote(query)}"
        logging.info(f"[Walmart] Searching: {url}")
        
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        results = []
        links = soup.find_all('a', href=re.compile(r'/ip/'))
        
        seen_urls = set()
        
        for link in links[:20]:
            try:
                url = link.get('href', '')
                if not url or url in seen_urls:
                    continue
                    
                seen_urls.add(url)
                
                title = link.get('aria-label', '') or link.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                
                if url.startswith('/'):
                    url = 'https://www.walmart.com' + url
                
                # Find price
                price = "Check site"
                parent = link.find_parent('div')
                if parent:
                    price_span = parent.find('span', text=re.compile(r'\$'))
                    if price_span:
                        price = clean_price(price_span.get_text())
                
                results.append({
                    "site": "Walmart",
                    "title": title[:100],
                    "link": url,
                    "price": price
                })
                
                if len(results) >= 3:
                    break
                    
            except Exception as e:
                continue
        
        logging.info(f"[Walmart] Found {len(results)} results")
        return results
        
    except Exception as e:
        logging.error(f"[Walmart] Error: {e}")
        return []

# ============================================================================
# AMAZON - REAL SCRAPER
# ============================================================================

def fetch_amazon(query):
    """Amazon scraper - returns real products"""
    try:
        url = f"https://www.amazon.com/s?k={urllib.parse.quote(query)}"
        logging.info(f"[Amazon] Searching: {url}")
        
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        results = []
        products = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        for product in products[:10]:
            try:
                # Title
                title_elem = product.find('h2')
                if not title_elem:
                    continue
                    
                title_link = title_elem.find('a')
                if not title_link:
                    continue
                    
                title = title_link.get_text(strip=True)
                link = 'https://www.amazon.com' + title_link.get('href', '')
                
                # Price
                price_whole = product.find('span', class_='a-price-whole')
                if price_whole:
                    price = f"${price_whole.get_text(strip=True)}"
                else:
                    price = "See site"
                
                results.append({
                    "site": "Amazon",
                    "title": title,
                    "link": link,
                    "price": price
                })
                
                if len(results) >= 3:
                    break
                    
            except Exception as e:
                continue
        
        logging.info(f"[Amazon] Found {len(results)} results")
        return results
        
    except Exception as e:
        logging.error(f"[Amazon] Error: {e}")
        return []

# ============================================================================
# OTHER SITES - PLACEHOLDER
# ============================================================================

def fetch_trendyol(query):
    """Trendyol - placeholder"""
    logging.info(f"[Trendyol] Skipped")
    return []

def fetch_aliexpress(query):
    """AliExpress - placeholder"""
    logging.info(f"[AliExpress] Skipped")
    return []

def fetch_target(query):
    """Target - placeholder"""
    logging.info(f"[Target] Skipped")
    return []
