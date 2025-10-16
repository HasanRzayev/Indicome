#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOOGLE CUSTOM SEARCH API - Smart Product Search
- 1 API request for ALL sites
- Filter results (cheapest, most expensive, etc.)
- Extract site names
"""

import requests
import logging
import re
from config import GOOGLE_API_KEY, GOOGLE_SEARCH_ENGINE_ID

logging.basicConfig(level=logging.INFO)

def extract_price_value(price_str):
    """Extract numeric price for sorting"""
    if not price_str or price_str == "Check site":
        return 999999  # Put at end
    
    # Extract number from $123.45 or 123.45 AZN etc
    match = re.search(r'(\d+[.,]?\d*)', price_str.replace(',', ''))
    if match:
        try:
            return float(match.group(1))
        except:
            return 999999
    return 999999

def extract_site_name(url):
    """Extract site name from URL"""
    try:
        # amazon.com, ebay.com, etc
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            domain = match.group(1)
            # Remove .com, .az, etc
            site = domain.split('.')[0]
            return site.capitalize()
        return "Shop"
    except:
        return "Shop"

def fetch_google_shopping(query, num_results=20):
    """
    Google Custom Search API - Get products from E-COMMERCE sites only
    Filters for Amazon, eBay, Walmart, Etsy, AliExpress product pages
    Uses ONLY 1 API request!
    """
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        
        # Search ONLY on e-commerce sites with product keywords
        search_query = f"{query} (site:amazon.com OR site:ebay.com OR site:walmart.com OR site:etsy.com OR site:aliexpress.com OR site:bestbuy.com OR site:newegg.com) (buy OR price OR product OR shop)"
        
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_SEARCH_ENGINE_ID,
            'q': search_query,
            'num': 10,  # Max 10 per request
        }
        
        logging.info(f"[Google] Searching: {query}")
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            logging.error(f"[Google] Error {response.status_code}: {response.text}")
        return []

        data = response.json()
        
        if 'items' not in data:
            logging.warning(f"[Google] No results found")
        return []

        results = []

        for item in data['items']:
            try:
                title = item.get('title', '').strip()
                link = item.get('link', '')
                snippet = item.get('snippet', '')
                
                # Skip if title too short
                if len(title) < 15:
                continue

                # FILTER: Only product pages (not category/homepage)
                # Amazon: /dp/, /gp/product/
                # eBay: /itm/, /p/
                # Walmart: /ip/
                # Etsy: /listing/
                # Best Buy: /site/...sku
                product_indicators = ['/dp/', '/gp/product/', '/itm/', '/p/', '/ip/', '/listing/', 'sku=', '/product/']
                
                # Skip if not a product page
                if not any(indicator in link for indicator in product_indicators):
                    logging.debug(f"[Google] Skipping non-product page: {link}")
            continue

                # Extract site name from URL
                site_name = extract_site_name(link)
                
                # Try to find price in title or snippet
                price = "Check site"
                
                # Look for price patterns
                for text in [title, snippet]:
                    # $123.45, $123, £45, €50
                    price_match = re.search(r'[\$£€₼]\s*(\d+[.,]?\d*)', text)
                    if price_match:
                        price = f"${price_match.group(1)}"
                        break
                    
                    # 123.45$ format
                    price_match = re.search(r'(\d+[.,]?\d*)\s*[\$£€₼]', text)
                    if price_match:
                        price = f"${price_match.group(1)}"
                        break

                results.append({
                    "site": site_name,
                    "title": title[:150],
                    "link": link,
                    "price": price,
                    "price_value": extract_price_value(price)  # For sorting
                })
                
            except Exception as e:
                logging.debug(f"[Google] Item error: {e}")
                continue

        logging.info(f"[Google] Found {len(results)} products from various sites")
        return results

    except Exception as e:
        logging.error(f"[Google] Error: {e}")
        return []

def filter_results(results, filter_type="all"):
    """
    Filter and sort results
    
    filter_type options:
    - "all": All results (default)
    - "cheapest": Cheapest first
    - "expensive": Most expensive first
    - "top3_cheap": Top 3 cheapest
    - "top5_cheap": Top 5 cheapest
    """
    if not results:
        return []
    
    if filter_type == "cheapest":
        # Sort by price, cheapest first
        return sorted(results, key=lambda x: x['price_value'])
    
    elif filter_type == "expensive":
        # Sort by price, most expensive first
        return sorted(results, key=lambda x: x['price_value'], reverse=True)
    
    elif filter_type == "top3_cheap":
        # Get 3 cheapest
        sorted_results = sorted(results, key=lambda x: x['price_value'])
        return sorted_results[:3]
    
    elif filter_type == "top5_cheap":
        # Get 5 cheapest
        sorted_results = sorted(results, key=lambda x: x['price_value'])
        return sorted_results[:5]
    
    else:  # "all" or default
        return results

# ============================================================================
# MAIN FUNCTION (Called by main.py)
# ============================================================================

def fetch_amazon(query):
    """
    Main search function
    Returns ALL results from Google (unsorted)
    """
    return fetch_google_shopping(query, num_results=10)

# Keep these for compatibility (not used anymore)
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
