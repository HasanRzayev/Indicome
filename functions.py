# -*- coding: utf-8 -*-
from supabase_client import supabase
import paypalrestsdk
import logging
from config import (
    PAYPAL_MODE, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET,
    PAYMENT_SUCCESS_URL, PAYMENT_CANCEL_URL, FREE_CREDITS_ON_SIGNUP
)

# ============================================================================
# PAYPAL CONFIGURATION
# ============================================================================

# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": PAYPAL_MODE,
    "client_id": PAYPAL_CLIENT_ID,
    "client_secret": PAYPAL_CLIENT_SECRET
})

# ============================================================================
# USER MANAGEMENT FUNCTIONS
# ============================================================================

def is_user_registered(telegram_id: int) -> bool:
    result = supabase.table("users").select("telegram_id").eq("telegram_id", telegram_id).execute()
    return len(result.data) > 0

def is_username_taken(username: str) -> bool:
    result = supabase.table("users").select("username").eq("username", username).execute()
    return len(result.data) > 0

def register_user(telegram_id: int, username: str):
    """Register a new user with free search credits"""
    supabase.table("users").insert({
        "telegram_id": telegram_id,
        "username": username,
        "search_count": 0,
        "search_credits": FREE_CREDITS_ON_SIGNUP  # Give 3 free searches
    }).execute()

def get_user_info(telegram_id: int):
    result = supabase.table("users").select("username", "search_count", "search_credits").eq("telegram_id", telegram_id).execute()
    return result.data[0] if result.data else None

def increment_search_count(telegram_id: int, count: int = 1):
    """Deduct search credits from user"""
    user_info = get_user_info(telegram_id)
    if user_info:
        credits = user_info.get("search_credits", 0)
        new_credits = max(0, credits - count)  # Don't go below 0
        
        supabase.table("users").update({
            "search_credits": new_credits,
            "search_count": user_info.get("search_count", 0) + count  # Keep track of total searches
        }).eq("telegram_id", telegram_id).execute()

def add_search_credits(telegram_id: int, credits: int):
    """Add search credits to user account"""
    try:
        user_info = get_user_info(telegram_id)
        if user_info:
            current_credits = user_info.get("search_credits", 0)
            new_credits = current_credits + credits
            
            supabase.table("users").update({
                "search_credits": new_credits
            }).eq("telegram_id", telegram_id).execute()
            
            logging.info(f"Added {credits} search credits to user {telegram_id}")
            return True
        return False
    except Exception as e:
        logging.error(f"Error adding search credits: {e}")
        return False

def get_available_searches(telegram_id: int) -> int:
    """Get available search credits for a user"""
    user_info = get_user_info(telegram_id)
    if not user_info:
        return 0
    
    return user_info.get("search_credits", 0)

def store_feedback(telegram_id: int, message: str):
    supabase.table("messages").insert({
        "telegram_id": telegram_id,
        "message": message
    }).execute()

def log_search_query(telegram_id: int, query: str):
    supabase.table("search_history").insert({
        "telegram_id": telegram_id,
        "query": query
    }).execute()

def convert_price_to_usd(raw_price: str) -> str:
    """Convert various currency formats to USD"""
    try:
        price = raw_price.strip()
        if "₼" in price or "AZN" in price:
            value = float(price.replace("₼", "").replace("AZN", "").replace(",", "").strip())
            usd = value / 1.7
        elif "₺" in price or "TRY" in price:
            value = float(price.replace("₺", "").replace("TRY", "").replace(",", "").strip())
            usd = value / 32
        elif "€" in price or "EUR" in price:
            value = float(price.replace("€", "").replace("EUR", "").replace(",", "").strip())
            usd = value * 1.1
        elif "$" in price:
            usd = float(price.replace("$", "").replace(",", "").strip())
        else:
            usd = float(price.replace(",", "").strip())
        return f"${usd:.2f}"
    except Exception:
        return raw_price

# ============================================================================
# PAYPAL PAYMENT FUNCTIONS
# ============================================================================

def create_paypal_payment(telegram_id: int, amount: float, credits: int = 0, description: str = None) -> str:
    """
    Create a PayPal payment and return the approval URL
    
    Args:
        telegram_id: User's Telegram ID
        amount: Payment amount in USD
        credits: Number of search credits
        description: Custom description for the payment
    
    Returns:
        PayPal approval URL or None if failed
    """
    try:
        item_name = f"{credits} Search Credits"
        item_sku = f"credits_{credits}"
        item_desc = description or f"{credits} product searches"
        
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": f"{PAYMENT_SUCCESS_URL}?telegram_id={telegram_id}",
                "cancel_url": f"{PAYMENT_CANCEL_URL}?telegram_id={telegram_id}"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": item_name,
                        "sku": item_sku,
                        "price": str(amount),
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(amount),
                    "currency": "USD"
                },
                "description": item_desc
            }]
        })

        if payment.create():
            # Store payment ID in database for later verification
            supabase.table("payments").insert({
                "telegram_id": telegram_id,
                "payment_id": payment.id,
                "amount": amount,
                "status": "pending",
                "payment_type": "credits",
                "credits": credits
            }).execute()
            
            logging.info(f"Created payment: {payment.id} for user {telegram_id} - {credits} credits")
            
            # Get approval URL
            for link in payment.links:
                if link.rel == "approval_url":
                    return link.href
        else:
            logging.error(f"PayPal payment creation failed: {payment.error}")
            return None
            
    except Exception as e:
        logging.error(f"PayPal payment error: {e}")
        return None

def execute_paypal_payment(payment_id: str, payer_id: str) -> bool:
    """
    Execute/complete a PayPal payment
    Returns True if successful, False otherwise
    """
    try:
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            # Update payment status in database
            supabase.table("payments").update({
                "status": "completed",
                "payer_id": payer_id
            }).eq("payment_id", payment_id).execute()
            
            return True
        else:
            logging.error(f"PayPal payment execution failed: {payment.error}")
            return False
            
    except Exception as e:
        logging.error(f"PayPal execution error: {e}")
        return False
