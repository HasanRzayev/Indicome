#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WORKING SCRAPERS ONLY - Tested and Verified
Sites: Amazon, Etsy, Kontakt.az, Tap.az
"""

import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import logging
import random
import time

logging.basicConfig(level=logging.INFO)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
]

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,az;q=0.8',
        'Connection': 'keep-alive',
    }

def make_request(url):
    try:
        time.sleep(random.uniform(0.3, 0.8))
        response = requests.get(url, headers=get_headers(), timeout=15)
        return response if response.status_code == 200 else None
    except:
        return None

def clean_price(text):
    if not text:
        return "See price"
    match = re.search(r'[\$€₼]?\s*(\d+[,.]?\d*)', text)
    return f"${match.group(1)}" if match else "See price"

def clean_title(text):
    return ' '.join(text.split())[:150] if text else ""

# ============================================================================
# AMAZON (Global - Works Great)
# ============================================================================

def fetch_amazon(query):
    try:
        url = f"https://www.amazon.com/s?k={urllib.parse.quote(query)}"
        logging.info(f"[Amazon] Searching: {query}")
        
        response = make_request(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        products = soup.select('[data-asin]:not([data-asin=""])')
        
        for product in products[:10]:
            try:
                asin = product.get('data-asin')
                if not asin or len(asin) != 10:
                    continue
                
                title_elem = product.select_one('h2 span')
                if not title_elem:
                    continue
                
                title = clean_title(title_elem.get_text())
                if len(title) < 15:
                    continue
                
                link = f"https://www.amazon.com/dp/{asin}"
                
                price_elem = product.select_one('.a-price-whole')
                price = clean_price(price_elem.get_text() if price_elem else "")
                
                results.append({
                    "site": "Amazon",
                    "title": title,
                    "link": link,
                    "price": price
                })
                
                if len(results) >= 3:
                    break
            except:
                continue
        
        logging.info(f"[Amazon] Found {len(results)} results")
        return results
    except:
        return []

# ============================================================================
# ETSY (Global Handmade - Simple HTML)
# ============================================================================

def fetch_etsy(query):
    try:
        url = f"https://www.etsy.com/search?q={urllib.parse.quote(query)}"
        logging.info(f"[Etsy] Searching: {query}")
        
        response = make_request(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        items = soup.select('[data-search-results-item]') or soup.select('div.v2-listing-card')
        
        for item in items[:10]:
            try:
                link_elem = item.select_one('a.listing-link') or item.select_one('a[href*="/listing/"]')
                if not link_elem:
                    continue
                
                link = link_elem.get('href', '')
                if not link.startswith('http'):
                    link = 'https://www.etsy.com' + link
                
                title_elem = item.select_one('h3') or item.select_one('[class*="title"]')
                if not title_elem:
                    continue
                
                title = clean_title(title_elem.get_text())
                if len(title) < 10:
                    continue
                
                price_elem = item.select_one('.currency-value') or item.select_one('[class*="price"]')
                price = clean_price(price_elem.get_text() if price_elem else "")
                
                results.append({
                    "site": "Etsy",
                    "title": title,
                    "link": link.split('?')[0],
                    "price": price
                })
                
                if len(results) >= 3:
                    break
            except:
                continue
        
        logging.info(f"[Etsy] Found {len(results)} results")
        return results
    except:
        return []

# ============================================================================
# KONTAKT.AZ (Azerbaijan Electronics)
# ============================================================================

def fetch_kontakt(query):
    try:
        url = f"https://kontakt.az/az/products?search={urllib.parse.quote(query)}"
        logging.info(f"[Kontakt.az] Searching: {query}")
        
        response = make_request(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        items = soup.select('.products-i') or soup.select('[class*="product"]')
        
        for item in items[:10]:
            try:
                link_elem = item.select_one('a[href*="/az/product/"]')
                if not link_elem:
                    continue
                
                link = link_elem.get('href', '')
                if not link.startswith('http'):
                    link = 'https://kontakt.az' + link
                
                title_elem = item.select_one('.products-i-title') or item.select_one('[class*="title"]')
                if not title_elem:
                    continue
                
                title = clean_title(title_elem.get_text())
                if len(title) < 5:
                    continue
                
                price_elem = item.select_one('.products-i-price') or item.select_one('[class*="price"]')
                price_text = price_elem.get_text() if price_elem else ""
                
                # Kontakt uses AZN
                price_match = re.search(r'(\d+[,.]?\d*)', price_text)
                if price_match:
                    azn_price = price_match.group(1).replace(',', '')
                    try:
                        usd_price = float(azn_price) / 1.7  # AZN to USD
                        price = f"${usd_price:.2f}"
                    except:
                        price = f"{azn_price} AZN"
                else:
                    price = "See price"
                
                results.append({
                    "site": "Kontakt.az",
                    "title": title,
                    "link": link,
                    "price": price
                })
                
                if len(results) >= 3:
                    break
            except:
                continue
        
        logging.info(f"[Kontakt.az] Found {len(results)} results")
        return results
    except:
        return []

# ============================================================================
# TAP.AZ (Azerbaijan Classifieds)
# ============================================================================

def fetch_tap(query):
    try:
        url = f"https://tap.az/elanlar?keywords={urllib.parse.quote(query)}"
        logging.info(f"[Tap.az] Searching: {query}")
        
        response = make_request(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        items = soup.select('.products-i') or soup.select('[class*="lot-"]')
        
        for item in items[:10]:
            try:
                link_elem = item.select_one('a[href*="/elanlar/"]')
                if not link_elem:
                    continue
                
                link = link_elem.get('href', '')
                if not link.startswith('http'):
                    link = 'https://tap.az' + link
                
                title_elem = item.select_one('.products_name') or item.select_one('[class*="title"]')
                if not title_elem:
                    continue
                
                title = clean_title(title_elem.get_text())
                if len(title) < 5:
                    continue
                
                price_elem = item.select_one('.price-val') or item.select_one('[class*="price"]')
                price_text = price_elem.get_text() if price_elem else ""
                
                # Tap.az uses AZN
                price_match = re.search(r'(\d+[,.]?\d*)', price_text)
                if price_match:
                    azn_price = price_match.group(1).replace(',', '').replace(' ', '')
                    try:
                        usd_price = float(azn_price) / 1.7
                        price = f"${usd_price:.2f}"
                    except:
                        price = f"{azn_price} AZN"
                else:
                    price = "See price"
                
                results.append({
                    "site": "Tap.az",
                    "title": title,
                    "link": link,
                    "price": price
                })
                
                if len(results) >= 2:
                    break
            except:
                continue
        
        logging.info(f"[Tap.az] Found {len(results)} results")
        return results
    except:
        return []

# ============================================================================
# REMOVED NON-WORKING SCRAPERS
# ============================================================================
# eBay - Blocks scraping
# Walmart - Blocks scraping  
# Trendyol - Requires JavaScript
# AliExpress - Requires JavaScript
# Target - Requires JavaScript

# Keeping these as empty to avoid errors in main.py
def fetch_ebay(query):
    logging.info(f"[eBay] Removed (blocks scraping)")
    return []

def fetch_walmart(query):
    logging.info(f"[Walmart] Removed (blocks scraping)")
    return []

def fetch_trendyol(query):
    logging.info(f"[Trendyol] Removed (requires JS)")
    return []

def fetch_aliexpress(query):
    logging.info(f"[AliExpress] Removed (requires JS)")
    return []

def fetch_target(query):
    logging.info(f"[Target] Removed (requires JS)")
    return []
