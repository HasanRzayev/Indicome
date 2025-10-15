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
PAYPAL_CLIENT_ID = "YOUR_PAYPAL_CLIENT_ID"
PAYPAL_CLIENT_SECRET = "YOUR_PAYPAL_CLIENT_SECRET"

# Payment redirect URLs
PAYMENT_SUCCESS_URL = "https://your-domain.com/payment/success"
PAYMENT_CANCEL_URL = "https://your-domain.com/payment/cancel"

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

