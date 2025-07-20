from supabase_client import supabase

def is_user_registered(telegram_id: int) -> bool:
    result = supabase.table("users").select("telegram_id").eq("telegram_id", telegram_id).execute()
    return len(result.data) > 0

def is_username_taken(username: str) -> bool:
    result = supabase.table("users").select("username").eq("username", username).execute()
    return len(result.data) > 0

def register_user(telegram_id: int, username: str):
    supabase.table("users").insert({
        "telegram_id": telegram_id,
        "username": username,
        "is_vip": False,
        "search_count": 0
    }).execute()

def get_user_info(telegram_id: int):
    result = supabase.table("users").select("username", "is_vip", "search_count").eq("telegram_id", telegram_id).execute()
    return result.data[0] if result.data else None

def increment_search_count(telegram_id: int, count: int = 1):
    user_info = get_user_info(telegram_id)
    if user_info:
        new_count = user_info["search_count"] + count
        supabase.table("users").update({"search_count": new_count}).eq("telegram_id", telegram_id).execute()

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
