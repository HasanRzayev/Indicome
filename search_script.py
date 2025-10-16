#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REAL WORKING SCRAPERS - Minimal and Reliable
"""

import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import logging

logging.basicConfig(level=logging.INFO)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def clean_price(text):
    if not text:
        return "Check site"
    match = re.search(r'\$?\s*(\d+[,.]?\d*)', text)
    if match:
        return f"${match.group(1)}"
    return "Check site"

# ============================================================================
# EBAY
# ============================================================================

def fetch_ebay(query):
    try:
        url = f"https://www.ebay.com/sch/i.html?_nkw={urllib.parse.quote(query)}"
        logging.info(f"[eBay] {url}")
        
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        results = []
        items = soup.find_all('li', class_='s-item')
        
        for item in items[:10]:
            try:
                title_elem = item.find('div', class_='s-item__title')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                if 'Shop on eBay' in title:
                    continue
                
                link_elem = item.find('a', class_='s-item__link')
                if not link_elem:
                    continue
                link = link_elem.get('href', '')
                
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
            except:
                continue
        
        logging.info(f"[eBay] {len(results)} results")
        return results
    except:
        return []

# ============================================================================
# WALMART
# ============================================================================

def fetch_walmart(query):
    try:
        url = f"https://www.walmart.com/search?q={urllib.parse.quote(query)}"
        logging.info(f"[Walmart] {url}")
        
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        results = []
        links = soup.find_all('a', href=re.compile(r'/ip/'))
        
        seen = set()
        for link in links[:20]:
            try:
                href = link.get('href', '')
                if not href or href in seen:
                    continue
                seen.add(href)
                
                title = link.get('aria-label', '') or link.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                
                if href.startswith('/'):
                    href = 'https://www.walmart.com' + href
                
                price = "Check site"
                
                results.append({
                    "site": "Walmart",
                    "title": title[:100],
                    "link": href.split('?')[0],  # Remove query params
                    "price": price
                })
                
                if len(results) >= 3:
                    break
            except:
                continue
        
        logging.info(f"[Walmart] {len(results)} results")
        return results
    except:
        return []

# ============================================================================
# AMAZON
# ============================================================================

def fetch_amazon(query):
    try:
        url = f"https://www.amazon.com/s?k={urllib.parse.quote(query)}"
        logging.info(f"[Amazon] {url}")
        
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        results = []
        products = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        for product in products[:10]:
            try:
                h2 = product.find('h2')
                if not h2:
                    continue
                
                link_tag = h2.find('a')
                if not link_tag:
                    continue
                
                title = link_tag.get_text(strip=True)
                href = link_tag.get('href', '')
                
                if href.startswith('/'):
                    href = 'https://www.amazon.com' + href
                
                # Clean Amazon link
                if '/dp/' in href or '/gp/' in href:
                    href = href.split('?')[0]  # Remove tracking
                
                price_elem = product.find('span', class_='a-price-whole')
                price = f"${price_elem.get_text(strip=True)}" if price_elem else "Check site"
                
                results.append({
                    "site": "Amazon",
                    "title": title,
                    "link": href,
                    "price": price
                })
                
                if len(results) >= 3:
                    break
            except:
                continue
        
        logging.info(f"[Amazon] {len(results)} results")
        return results
    except:
        return []

# ============================================================================
# OTHER SITES - PLACEHOLDER
# ============================================================================

def fetch_trendyol(query):
    logging.info(f"[Trendyol] Skipped (requires JS)")
    return []

def fetch_aliexpress(query):
    logging.info(f"[AliExpress] Skipped (requires JS)")
    return []

def fetch_target(query):
    logging.info(f"[Target] Skipped (requires JS)")
    return []
