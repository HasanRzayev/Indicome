#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOOGLE CUSTOM SEARCH - MULTI-SITE DIVERSITY
Gets products from Amazon, eBay, Walmart, BestBuy, Etsy, Newegg, AliExpress
"""

import requests
import logging
import re
from config import GOOGLE_API_KEY, GOOGLE_SEARCH_ENGINE_ID

logging.basicConfig(level=logging.INFO)

def extract_site_name(url):
    """Extract clean site name from URL"""
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

def _search_group(query, sites, max_results=5):
    """Search a group of sites"""
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        
        site_filter = " OR ".join([f"site:{site}" for site in sites])
        search_query = f"{query} ({site_filter})"
        
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_SEARCH_ENGINE_ID,
            'q': search_query,
            'num': max_results
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        
        if 'items' not in data:
            return []
        
        results = []
        
        for item in data['items']:
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
        
    except:
        return []

def fetch_google_shopping(query):
    """
    Main search function - Gets products from MULTIPLE sites
    Makes 3 API calls to ensure diversity
    """
    try:
        all_results = []
        
        logging.info(f"[Google] Searching {query} on multiple sites...")
        
        # Group 1: Amazon + eBay (most popular)
        group1 = _search_group(query, ["amazon.com", "ebay.com"], max_results=4)
        all_results.extend(group1)
        logging.info(f"[Google] Group 1 (Amazon/eBay): {len(group1)} results")
        
        # Group 2: Walmart + BestBuy
        group2 = _search_group(query, ["walmart.com", "bestbuy.com"], max_results=3)
        all_results.extend(group2)
        logging.info(f"[Google] Group 2 (Walmart/BestBuy): {len(group2)} results")
        
        # Group 3: Etsy + Newegg + AliExpress
        group3 = _search_group(query, ["etsy.com", "newegg.com", "aliexpress.com"], max_results=3)
        all_results.extend(group3)
        logging.info(f"[Google] Group 3 (Etsy/Newegg/AliExpress): {len(group3)} results")
        
        logging.info(f"[Google] TOTAL: {len(all_results)} products from all sites")
        return all_results
        
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
