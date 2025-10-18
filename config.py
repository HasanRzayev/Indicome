# -*- coding: utf-8 -*-
# ============================================================================
# BOT CONFIGURATION
# ============================================================================

BOT_TOKEN = "8051783595:AAENND4Ck3l7z1mao6WKxBYdrv2gskVmKzM"

# ============================================================================
# ADMIN NOTIFICATION CONFIGURATION
# ============================================================================

ADMIN_BOT_TOKEN = "7801764151:AAEeBB-SBAJEz0zAKhLPHKp6Ty8EeHBLuCQ"
ADMIN_TELEGRAM_ID = 8093025085  # Your Telegram ID for notifications

# ============================================================================
# PAYPAL CONFIGURATION
# ============================================================================

PAYPAL_MODE = "sandbox"  # "sandbox" for testing, "live" for production
PAYPAL_CLIENT_ID = "AaTBl7vZ-aaxFG1sRvvKM1rMxkB_An5-kCdvW42Fgry3t0ZgiWM2kM0XjkflPj2KwY5E4yzr7VZBditA"
PAYPAL_CLIENT_SECRET = "EGbnhZIYwzE-XX4FR0wrguw4nW8iJuyLUpxI_vilIl5_pPpZuvOjKcfkWH0HSqxDja1yR4oz67w5lr0B"

# Payment redirect URLs (Telegram bot doesn't need real URLs, but PayPal requires them)
# You can use a simple static page or just return to a thank you message
PAYMENT_SUCCESS_URL = "https://t.me/your_bot_username?start=payment_success"
PAYMENT_CANCEL_URL = "https://t.me/your_bot_username?start=payment_cancelled"

# ============================================================================
# CREDIT PACKAGES
# ============================================================================

CREDIT_PACKAGES = {
    "starter": {
        "name": "Starter Pack",
        "credits": 5,
        "price": 2.99
    },
    "basic": {
        "name": "Basic Pack",
        "credits": 15,
        "price": 7.99
    },
    "premium": {
        "name": "Premium Pack",
        "credits": 50,
        "price": 19.99
    },
    "ultimate": {
        "name": "Ultimate Pack",
        "credits": 150,
        "price": 49.99
    }
}

# ============================================================================
# FREE CREDITS ON REGISTRATION
# ============================================================================

FREE_CREDITS_ON_SIGNUP = 3  # Give 3 free searches on registration

# ============================================================================
# GOOGLE CUSTOM SEARCH API (100 queries/day FREE per API)
# Multiple APIs for backup/failover - 300 queries/day total!
# ============================================================================

GOOGLE_API_KEYS = [
    {
        "api_key": "AIzaSyBnqNw2vfrlsh3Rh6kCtp8yTg-3f4_3Q9U",
        "search_engine_id": "91efad1f41ff34b14",
        "name": "API 1"
    },
    {
        "api_key": "AIzaSyDHR8LZ_5VTode_I6v904pHL35wkyfgNrk",
        "search_engine_id": "2078eb15f7d8b4b46",
        "name": "API 2"
    },
    {
        "api_key": "AIzaSyBazy-8ouqKiBn_LN_DGZk8Noz5GoRl9Xk",
        "search_engine_id": "4525b4748c4de43a3",
        "name": "API 3"
    }
]

# Backward compatibility
GOOGLE_API_KEY = GOOGLE_API_KEYS[0]["api_key"]
GOOGLE_SEARCH_ENGINE_ID = GOOGLE_API_KEYS[0]["search_engine_id"]

