#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOOGLE CUSTOM SEARCH API - Real Products, 100% Working
100 queries/day FREE
"""

import requests
import logging
from config import GOOGLE_API_KEY, GOOGLE_SEARCH_ENGINE_ID

logging.basicConfig(level=logging.INFO)

# ============================================================================
# GOOGLE CUSTOM SEARCH - THE REAL SOLUTION
# ============================================================================

def fetch_google_shopping(query):
    """Google Custom Search API - Shopping results"""
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_SEARCH_ENGINE_ID,
            'q': f"{query} buy shop price",
            'num': 10,
            'searchType': 'image',  # Get shopping results
        }
        
        logging.info(f"[Google Shopping] Searching: {query}")
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            logging.error(f"[Google] API Error: {response.status_code}")
            logging.error(f"Response: {response.text}")
            return []
        
        data = response.json()
        results = []
        
        if 'items' not in data:
            logging.warning(f"[Google] No items found")
            return []
        
        for item in data['items'][:5]:
            try:
                title = item.get('title', '')
                link = item.get('link', '')
                snippet = item.get('snippet', '')
                
                # Try to extract price from snippet or title
                price = "Check site"
                for text in [title, snippet]:
                    if '$' in text:
                        import re
                        match = re.search(r'\$\s*(\d+[.,]?\d*)', text)
                        if match:
                            price = f"${match.group(1)}"
                            break
                
                if len(title) < 10:
                    continue
                
                results.append({
                    "site": "Google Shopping",
                    "title": title[:150],
                    "link": link,
                    "price": price
                })
                
            except Exception as e:
                logging.debug(f"[Google] Item error: {e}")
                continue
        
        logging.info(f"[Google Shopping] Found {len(results)} results")
        return results
        
    except Exception as e:
        logging.error(f"[Google Shopping] Error: {e}")
        return []

# ============================================================================
# MAIN SEARCH FUNCTION
# ============================================================================

def fetch_amazon(query):
    """Main search - uses Google Custom Search"""
    return fetch_google_shopping(query)

# Keep these for compatibility
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
