#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOOGLE CUSTOM SEARCH - 3 API FAILOVER SYSTEM
300 queries/day total! Auto-switches when one API quota runs out.
"""

import requests
import logging
import re
from config import GOOGLE_API_KEYS

logging.basicConfig(level=logging.INFO)

# Track current API (rotates automatically)
current_api_index = 0

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
    if not price_str or "Check" in price_str:
        return 999999
    
    match = re.search(r'(\d+[.,]?\d*)', price_str.replace(',', ''))
    if match:
        try:
            return float(match.group(1))
        except:
            return 999999
    return 999999

def _make_api_request(query, sites, max_results, api_config):
    """Make single API request"""
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        
        site_filter = " OR ".join([f"site:{site}" for site in sites])
        search_query = f"{query} ({site_filter})"
        
        params = {
            'key': api_config['api_key'],
            'cx': api_config['search_engine_id'],
            'q': search_query,
            'num': max_results
        }
        
        response = requests.get(url, params=params, timeout=15)
        return response
        
    except Exception as e:
        logging.error(f"API request error: {e}")
        return None

def _parse_items(items):
    """Parse Google search items"""
    results = []
    
    for item in items:
        try:
            title = item.get('title', '').strip()
            link = item.get('link', '')
            snippet = item.get('snippet', '')
            
            if len(title) < 15 or not link:
                continue
            
            # Only product pages
            product_indicators = ['/dp/', '/gp/', '/itm/', '/p/', '/ip/', '/listing/', 'sku=', '/product/', '/item/']
            
            if not any(ind in link for ind in product_indicators):
                continue
            
            site_name = extract_site_name(link)
            
            # Extract price
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
            
        except:
            continue
    
    return results

def _search_with_failover(query, sites, max_results=5):
    """Search with automatic API failover"""
    global current_api_index
    
    # Try all 3 APIs
    for attempt in range(len(GOOGLE_API_KEYS)):
        api_config = GOOGLE_API_KEYS[current_api_index]
        
        logging.info(f"[Google] Trying {api_config['name']}...")
        
        response = _make_api_request(query, sites, max_results, api_config)
        
        if not response:
            current_api_index = (current_api_index + 1) % len(GOOGLE_API_KEYS)
            continue
        
        # Success!
        if response.status_code == 200:
            data = response.json()
            
            if 'items' in data:
                results = _parse_items(data['items'])
                logging.info(f"[Google] {api_config['name']} SUCCESS - {len(results)} products")
                return results
            else:
                logging.warning(f"[Google] {api_config['name']} - no items")
                return []
        
        # Quota exceeded - try next API
        elif response.status_code == 429:
            logging.warning(f"[Google] {api_config['name']} QUOTA EXCEEDED - switching to next API")
            current_api_index = (current_api_index + 1) % len(GOOGLE_API_KEYS)
            continue
        
        # Other error - try next API
        else:
            logging.error(f"[Google] {api_config['name']} error {response.status_code}")
            current_api_index = (current_api_index + 1) % len(GOOGLE_API_KEYS)
            continue
    
    # All APIs failed
    logging.error("[Google] ALL 3 APIs FAILED!")
    return []

def fetch_google_shopping(query):
    """
    Main search - Gets products from 7 e-commerce sites
    Uses 3 API calls with automatic failover
    Total: 300 queries/day (100 per API)
    """
    try:
        all_results = []
        
        logging.info(f"[Google] Starting multi-site search for: {query}")
        
        # Group 1: Amazon + eBay
        group1 = _search_with_failover(query, ["amazon.com", "ebay.com"], max_results=4)
        all_results.extend(group1)
        logging.info(f"[Google] Amazon/eBay: {len(group1)} products")
        
        # Group 2: Walmart + BestBuy
        group2 = _search_with_failover(query, ["walmart.com", "bestbuy.com"], max_results=3)
        all_results.extend(group2)
        logging.info(f"[Google] Walmart/BestBuy: {len(group2)} products")
        
        # Group 3: Etsy + Newegg + AliExpress
        group3 = _search_with_failover(query, ["etsy.com", "newegg.com", "aliexpress.com"], max_results=3)
        all_results.extend(group3)
        logging.info(f"[Google] Etsy/Newegg/AliExpress: {len(group3)} products")
        
        logging.info(f"[Google] TOTAL: {len(all_results)} products from all sites")
        return all_results
        
    except Exception as e:
        logging.error(f"[Google] Main error: {e}")
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
        return sorted(results, key=lambda x: x['price_value'])[:3]
    elif filter_type == "top5_cheap":
        return sorted(results, key=lambda x: x['price_value'])[:5]
    else:
        return results

# ============================================================================
# COMPATIBILITY
# ============================================================================

def fetch_amazon(query):
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
