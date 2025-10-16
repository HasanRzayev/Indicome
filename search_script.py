#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOOGLE CUSTOM SEARCH - E-COMMERCE ONLY
Clean, Working, Production-Ready
"""

import requests
import logging
import re
from config import GOOGLE_API_KEY, GOOGLE_SEARCH_ENGINE_ID

logging.basicConfig(level=logging.INFO)

def extract_site_name(url):
    """Extract site name from URL"""
    try:
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            domain = match.group(1)
            site = domain.split('.')[0]
            return site.capitalize()
        return "Shop"
    except:
        return "Shop"

def extract_price_value(price_str):
    """Extract numeric price for sorting"""
    if not price_str or "Check" in price_str or "See" in price_str:
        return 999999
    
    match = re.search(r'(\d+[.,]?\d*)', price_str.replace(',', ''))
    if match:
        try:
            return float(match.group(1))
        except:
            return 999999
    return 999999

def fetch_google_shopping(query):
    """Google Custom Search - E-commerce sites only"""
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        
        # Search ONLY e-commerce sites
        search_query = f"{query} (site:amazon.com OR site:ebay.com OR site:walmart.com OR site:etsy.com OR site:aliexpress.com OR site:bestbuy.com OR site:newegg.com)"
        
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_SEARCH_ENGINE_ID,
            'q': search_query,
            'num': 10
        }
        
        logging.info(f"[Google] Searching: {query}")
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            logging.error(f"[Google] API Error {response.status_code}")
            return []
        
        data = response.json()
        
        if 'items' not in data:
            logging.warning("[Google] No items in response")
            return []
        
        results = []
        
        for item in data['items']:
            try:
                title = item.get('title', '').strip()
                link = item.get('link', '')
                snippet = item.get('snippet', '')
                
                if len(title) < 15 or not link:
                    continue
                
                # Filter: Only product pages
                product_indicators = ['/dp/', '/gp/product/', '/itm/', '/p/', '/ip/', '/listing/', 'sku=', '/product/', '/item/']
                
                if not any(ind in link for ind in product_indicators):
                    continue
                
                site_name = extract_site_name(link)
                
                # Find price in title or snippet
                price = "Check site"
                
                for text in [title, snippet]:
                    price_match = re.search(r'[\$£€]\s*(\d+[.,]?\d*)', text)
                    if price_match:
                        price = f"${price_match.group(1)}"
                        break
                
                results.append({
                    "site": site_name,
                    "title": title[:150],
                    "link": link,
                    "price": price,
                    "price_value": extract_price_value(price)
                })
                
            except Exception as e:
                logging.debug(f"[Google] Item error: {e}")
                continue
        
        logging.info(f"[Google] Found {len(results)} product pages")
        return results
        
    except Exception as e:
        logging.error(f"[Google] Error: {e}")
        return []

def filter_results(results, filter_type="all"):
    """Filter and sort results"""
    if not results:
        return []
    
    if filter_type == "cheapest":
        return sorted(results, key=lambda x: x['price_value'])
    
    elif filter_type == "expensive":
        return sorted(results, key=lambda x: x['price_value'], reverse=True)
    
    elif filter_type == "top3_cheap":
        sorted_results = sorted(results, key=lambda x: x['price_value'])
        return sorted_results[:3]
    
    elif filter_type == "top5_cheap":
        sorted_results = sorted(results, key=lambda x: x['price_value'])
        return sorted_results[:5]
    
    else:
        return results

# ============================================================================
# COMPATIBILITY FUNCTIONS (for main.py)
# ============================================================================

def fetch_amazon(query):
    """Main search - uses Google"""
    return fetch_google_shopping(query)

def fetch_ebay(query):
    return []

def fetch_walmart(query):
    return []

def fetch_etsy(query):
    return []

def fetch_trendyol(query):
    return []

def fetch_aliexpress(query):
    return []

def fetch_target(query):
    return []
