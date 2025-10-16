#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIMPLEST WORKING SCRAPER - Amazon Only
100% Free, 100% Working
"""

import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging

logging.basicConfig(level=logging.INFO)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# ============================================================================
# AMAZON - THE ONLY ONE THAT WORKS
# ============================================================================

def fetch_amazon(query):
    """Amazon scraper - Simple and working"""
    try:
        url = f"https://www.amazon.com/s?k={urllib.parse.quote(query)}"
        logging.info(f"[Amazon] Searching: {query}")
        
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            logging.error(f"[Amazon] Status: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Find products with ASIN
        products = soup.find_all('div', {'data-asin': True})
        
        for product in products[:15]:
            asin = product.get('data-asin', '')
            
            # Skip if no valid ASIN
            if not asin or len(asin) != 10:
                continue
            
            # Get title
            title_elem = product.find('h2')
            if not title_elem:
                continue
            
            title_text = title_elem.get_text(strip=True)
            
            # Skip if title too short
            if len(title_text) < 20:
                continue
            
            # Build link
            link = f"https://www.amazon.com/dp/{asin}"
            
            # Get price
            price_elem = product.find('span', class_='a-price-whole')
            if price_elem:
                price = f"${price_elem.get_text(strip=True)}"
            else:
                price = "See Amazon"
            
            results.append({
                "site": "Amazon",
                "title": title_text[:150],
                "link": link,
                "price": price
            })
            
            # Stop at 5 results
            if len(results) >= 5:
                break
        
        logging.info(f"[Amazon] Found {len(results)} products")
        return results
        
    except Exception as e:
        logging.error(f"[Amazon] Error: {e}")
        return []

# ============================================================================
# ALL OTHER SITES - DISABLED (DON'T WORK)
# ============================================================================

def fetch_ebay(query):
    return []

def fetch_walmart(query):
    return []

def fetch_etsy(query):
    return []

def fetch_kontakt(query):
    return []

def fetch_tap(query):
    return []

def fetch_trendyol(query):
    return []

def fetch_aliexpress(query):
    return []

def fetch_target(query):
    return []
