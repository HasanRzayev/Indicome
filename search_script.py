#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import logging
import re
from config import GOOGLE_API_KEYS

logging.basicConfig(level=logging.INFO)
current_api_index = 0

def extract_site_name(url):
    try:
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            return match.group(1).split('.')[0].capitalize()
        return "Shop"
    except:
        return "Shop"

def extract_price_value(price_str):
    if not price_str or "Check" in price_str:
        return 999999
    
    # Extract numeric value
    match = re.search(r'(\d+[.,]?\d*)', price_str.replace(',', ''))
    if match:
        try:
            value = float(match.group(1))
            # Convert AZN to USD for comparison (1 AZN ≈ 0.59 USD)
            if '₼' in price_str or 'AZN' in price_str or 'manat' in price_str.lower():
                value = value * 0.59  # Convert to USD equivalent
            return value
        except:
            return 999999
    return 999999

def _make_search_request(query, sites, max_results, api_config):
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        site_filter = " OR ".join([f"site:{s}" for s in sites])
        params = {
            'key': api_config['api_key'],
            'cx': api_config['search_engine_id'],
            'q': f"{query} ({site_filter})",
            'num': max_results
        }
        response = requests.get(url, params=params, timeout=15)
        return response
    except:
        return None

def _parse_search_items(items):
    results = []
    for item in items:
        try:
            title = item.get('title', '').strip()
            link = item.get('link', '')
            snippet = item.get('snippet', '')
            
            if len(title) < 15 or not link:
                continue
            
            if not any(i in link for i in ['/dp/', '/itm/', '/ip/', '/listing/', '/product/', '/products/', 'sku=']):
                continue
            
            site_name = extract_site_name(link)
            price = "Check site"
            
            # Check for various price formats
            for text in [title, snippet]:
                # Dollar prices
                m = re.search(r'[\$]\s*(\d+[.,]?\d*)', text)
                if m:
                    price = f"${m.group(1)}"
                    break
                # Manat/AZN prices (for Umico)
                m = re.search(r'(\d+[.,]?\d*)\s*[₼]', text)
                if m:
                    price = f"{m.group(1)} ₼"
                    break
                m = re.search(r'(\d+[.,]?\d*)\s*AZN', text, re.IGNORECASE)
                if m:
                    price = f"{m.group(1)} ₼"
                    break
                m = re.search(r'(\d+[.,]?\d*)\s*manat', text, re.IGNORECASE)
                if m:
                    price = f"{m.group(1)} ₼"
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

def _search_with_failover(query, sites, max_results):
    global current_api_index
    
    for attempt in range(len(GOOGLE_API_KEYS)):
        api = GOOGLE_API_KEYS[current_api_index]
        response = _make_search_request(query, sites, max_results, api)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'items' in data:
                    results = _parse_search_items(data['items'])
                    logging.info(f"[{api['name']}] {len(results)} products")
                    return results
            except:
                pass
        
        if response and response.status_code == 429:
            logging.warning(f"[{api['name']}] quota exceeded")
        
        current_api_index = (current_api_index + 1) % len(GOOGLE_API_KEYS)
    
    return []

def fetch_google_shopping(query, selected_site="all"):
    """
    Search products from selected site(s)
    
    Args:
        query: Search query
        selected_site: Site to search from (all, amazon, ebay, walmart, bestbuy, etsy, newegg, umico)
    """
    all_results = []
    
    site_map = {
        "amazon": ["amazon.com"],
        "ebay": ["ebay.com"],
        "walmart": ["walmart.com"],
        "bestbuy": ["bestbuy.com"],
        "etsy": ["etsy.com"],
        "newegg": ["newegg.com"],
        "umico": ["umico.az"]
    }
    
    if selected_site == "all":
        # Search all sites
        all_results.extend(_search_with_failover(query, ["amazon.com", "ebay.com"], 4))
        all_results.extend(_search_with_failover(query, ["walmart.com", "bestbuy.com"], 3))
        all_results.extend(_search_with_failover(query, ["etsy.com", "newegg.com"], 3))
        all_results.extend(_search_with_failover(query, ["umico.az"], 4))
    elif selected_site in site_map:
        # Search only selected site with more results
        all_results.extend(_search_with_failover(query, site_map[selected_site], 10))
    
    logging.info(f"[Google] Site: {selected_site}, Total: {len(all_results)} products")
    return all_results

def filter_results(results, filter_type="all"):
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
    return results

def fetch_amazon(query, selected_site="all"):
    return fetch_google_shopping(query, selected_site)

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
