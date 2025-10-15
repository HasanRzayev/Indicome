# -*- coding: utf-8 -*-
import logging
import asyncio
from collections import defaultdict
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)
from functions import (
    is_user_registered, is_username_taken, register_user,
    get_user_info, increment_search_count,
    store_feedback, log_search_query, convert_price_to_usd,
    create_paypal_payment, execute_paypal_payment,
    add_search_credits, get_available_searches
)
from search_script import fetch_ebay, fetch_walmart, fetch_amazon, fetch_trendyol, fetch_aliexpress, fetch_target
from config import BOT_TOKEN, CREDIT_PACKAGES

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Conversation states
MAIN_MENU, SIGNUP_USERNAME, LOGIN_USERNAME, GET_QUERY, GET_FEEDBACK = range(5)

# ============================================================================
# MENU BUILDERS
# ============================================================================

def main_menu_buttons():
    """Build main menu keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Search Products", callback_data="search")],
        [InlineKeyboardButton("💰 Buy Search Credits", callback_data="buy_credits")],
        [InlineKeyboardButton("💬 Feedback", callback_data="feedback")],
        [InlineKeyboardButton("🚪 Exit", callback_data="exit")]
    ])

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - Welcome message"""
    telegram_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or str(telegram_id)
    
    # Auto-register user if not exists
    user_info = get_user_info(telegram_id)
    if not user_info:
        register_user(telegram_id, username)
        user_info = get_user_info(telegram_id)
        is_new_user = True
    else:
        is_new_user = False
    
    # Get search credits
    search_credits = user_info.get('search_credits', 0)
    
    if is_new_user:
        status_msg = (
            f"═══════════════════════════\n"
            f"   👋 *Welcome {username}!*\n"
            f"═══════════════════════════\n\n"
            f"🎉 *You've received 3 FREE searches!*\n\n"
            f"🔍 *Product Search Bot*\n\n"
            f"Search products across:\n"
            f"   • eBay\n"
            f"   • Amazon\n"
            f"   • Walmart\n"
            f"   • AliExpress\n"
            f"   • Trendyol\n"
            f"   • Target\n\n"
            f"💰 *Your Search Credits: {search_credits}*\n\n"
            f"💡 Start searching now!"
        )
    else:
        status_msg = (
            f"═══════════════════════════\n"
            f"   👋 *Welcome back {username}!*\n"
            f"═══════════════════════════\n\n"
            f"💰 *Your Search Credits: {search_credits}*\n\n"
            f"🔍 Ready to search for products!"
        )
    
        await update.message.reply_text(
        status_msg,
        parse_mode="Markdown",
        reply_markup=main_menu_buttons()
        )
        return MAIN_MENU

# ============================================================================
# CALLBACK HANDLERS
# ============================================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries from inline buttons"""
    query = update.callback_query
    await query.answer()
    telegram_id = query.from_user.id
    data = query.data

    if data == "search":
        await query.edit_message_text("🔍 Enter the product name to search:")
        return GET_QUERY

    elif data == "feedback":
        await query.edit_message_text("💬 Please type your feedback and press Enter:")
        return GET_FEEDBACK
    
    elif data == "buy_credits":
        await show_credits_menu(update, context)
        return MAIN_MENU
    
    elif data.startswith("buy_package_"):
        package_key = data.replace("buy_package_", "")
        await handle_credits_purchase(update, context, package_key)
        return MAIN_MENU
    
    elif data == "back_to_menu":
        user_info = get_user_info(telegram_id)
        search_credits = user_info.get('search_credits', 0) if user_info else 0
        username = query.from_user.username or query.from_user.first_name or str(telegram_id)
        await query.edit_message_text(
            f"🏠 *Main Menu*\n\n"
            f"👋 Welcome {username}\n"
            f"💰 Search Credits: {search_credits}",
            parse_mode="Markdown",
            reply_markup=main_menu_buttons()
        )
        return MAIN_MENU

    elif data == "exit":
        await query.edit_message_text("👋 Thank you for using our bot. Goodbye!")
        return ConversationHandler.END

    return MAIN_MENU

async def show_credits_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available credit packages"""
    query = update.callback_query
    telegram_id = query.from_user.id
    
    # Build credit packages buttons
    buttons = []
    for key, package in CREDIT_PACKAGES.items():
        price_per_search = package['price'] / package['credits']
        button_text = f"{package['name']} - ${package['price']:.2f} (${price_per_search:.2f}/search)"
        buttons.append([InlineKeyboardButton(button_text, callback_data=f"buy_package_{key}")])
    
    buttons.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")])

    user_info = get_user_info(telegram_id)
    current_credits = user_info.get('search_credits', 0) if user_info else 0
    
    await query.edit_message_text(
        f"═══════════════════════════\n"
        f"   💰 *Buy Search Credits*\n"
        f"═══════════════════════════\n\n"
        f"Your Current Credits: *{current_credits}*\n\n"
        f"📦 *Available Packages:*\n"
        f"Choose a package below:\n\n"
        f"💡 1 credit = 1 product search\n"
        f"💡 Credits never expire!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_credits_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE, package_key: str):
    """Handle credit package purchase"""
    query = update.callback_query
    telegram_id = query.from_user.id
    
    if package_key not in CREDIT_PACKAGES:
        await query.edit_message_text(
            "❌ Invalid package selected.",
            reply_markup=main_menu_buttons()
        )
        return
    
    package = CREDIT_PACKAGES[package_key]
    
    try:
        payment_url = create_paypal_payment(
            telegram_id,
            package['price'],
            credits=package['credits'],
            description=f"{package['name']} - {package['credits']} searches"
        )
        
        if payment_url:
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Pay with PayPal", url=payment_url)],
                [InlineKeyboardButton("🔙 Back to Packages", callback_data="buy_credits")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
            ])
            
            await query.edit_message_text(
                f"═══════════════════════════\n"
                f"   💰 *{package['name']}*\n"
                f"═══════════════════════════\n\n"
                f"📦 *Package Details:*\n"
                f"  • Credits: {package['credits']} searches\n"
                f"  • Price: ${package['price']:.2f}\n"
                f"  • Per search: ${package['price']/package['credits']:.2f}\n\n"
                f"✨ *Benefits:*\n"
                f"  • Credits never expire\n"
                f"  • Use anytime you want\n"
                f"  • Instant activation\n\n"
                f"🔒 Secure payment via PayPal\n\n"
                f"Click below to complete purchase:",
                parse_mode="Markdown",
                reply_markup=buttons
            )
        else:
            await query.edit_message_text(
                "❌ Error creating payment. Please try again later.",
                reply_markup=main_menu_buttons()
            )
    except Exception as e:
        logging.error(f"PayPal payment creation error: {e}")
        await query.edit_message_text(
            "❌ Error processing your request. Please try again.",
        reply_markup=main_menu_buttons()
    )

# ============================================================================
# SEARCH HANDLER
# ============================================================================

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle product search query"""
    telegram_id = update.message.from_user.id
    query = update.message.text.strip()

    # Auto-register if not exists
    user_info = get_user_info(telegram_id)
    if user_info is None:
        username = update.message.from_user.username or update.message.from_user.first_name or str(telegram_id)
        register_user(telegram_id, username)
        user_info = get_user_info(telegram_id)

    # Check search credits
    search_credits = user_info.get("search_credits", 0)
    
    if search_credits <= 0:
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Buy Credits", callback_data="buy_credits")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
        ])
        
        await update.message.reply_text(
            f"🛑 *No search credits!*\n\n"
            f"Your Credits: {search_credits}\n\n"
            f"💡 Buy credits to start searching.\n"
            f"   Starting from $2.99 for 5 searches!",
            parse_mode="Markdown",
            reply_markup=buttons
        )
        return MAIN_MENU

    if not query or len(query) < 3:
        await update.message.reply_text("❓ Please enter a valid product name (e.g., *iPhone 15*)", parse_mode="Markdown")
        return GET_QUERY

    await update.message.reply_text(f"🔎 Searching for *{query}*...", parse_mode="Markdown")
    log_search_query(telegram_id, query)

    loop = asyncio.get_running_loop()
    tasks = [
        loop.run_in_executor(None, fetch_ebay, query),
        loop.run_in_executor(None, fetch_walmart, query),
        loop.run_in_executor(None, fetch_amazon, query),
        loop.run_in_executor(None, fetch_trendyol, query),
        loop.run_in_executor(None, fetch_aliexpress, query),
        loop.run_in_executor(None, fetch_target, query)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_products = []
    for res in results:
        if isinstance(res, Exception):
            logging.error(f"Search error: {res}")
            continue
        if isinstance(res, list):
            all_products.extend(res)

    if not all_products:
        await update.message.reply_text("😔 Sorry, no results found.", reply_markup=main_menu_buttons())
        return MAIN_MENU

    # Show one product per site (best result from each)
    products_by_site = defaultdict(list)
    for product in all_products:
        products_by_site[product["site"]].append(product)

    products_to_show = [products[0] for products in products_by_site.values() if products]

    for product in products_to_show:
        formatted_price = convert_price_to_usd(product["price"])
        msg = (
            f"🌐 *{product['site']}*\n"
            f"📦 *Product*: {product['title']}\n"
            f"💰 *Price*: {formatted_price}\n"
            f"🔗 [Link]({product['link']})"
        )
        await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=False)

    # Deduct 1 credit
    increment_search_count(telegram_id)
    
    # Show remaining credits
    remaining_credits = search_credits - 1
    await update.message.reply_text(
        f"✅ Search complete!\n💰 Remaining credits: {remaining_credits}",
        reply_markup=main_menu_buttons()
    )
    
    return MAIN_MENU

async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    feedback_text = update.message.text.strip()
    store_feedback(telegram_id, feedback_text)
    await update.message.reply_text("✅ Thank you for your feedback!", reply_markup=main_menu_buttons())
    return MAIN_MENU

# ============================================================================
# MAIN FUNCTION
# ============================================================================

if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(handle_callback)],
            GET_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query)],
            GET_FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback)],
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    print("✅ Bot started with PayPal credit system! 💰🎈")
    application.run_polling()
