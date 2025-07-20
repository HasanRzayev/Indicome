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
    store_feedback, log_search_query, convert_price_to_usd
)
from search_script import fetch_ebay, fetch_walmart, fetch_amazon, fetch_trendyol, fetch_aliexpress, fetch_target

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

MAIN_MENU, SIGNUP_USERNAME, LOGIN_USERNAME, GET_QUERY, GET_FEEDBACK = range(5)

def main_menu_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Search", callback_data="search")],
        [InlineKeyboardButton("💬 Feedback", callback_data="feedback")],
        [InlineKeyboardButton("🚪 Exit", callback_data="exit")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    user_info = get_user_info(telegram_id)

    if user_info:
        await update.message.reply_text(
            f"👋 Welcome back, {user_info.get('username', '')}!",
            reply_markup=main_menu_buttons()
        )
        return MAIN_MENU
    else:
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Sign Up", callback_data="signup")],
            [InlineKeyboardButton("🔐 Log In", callback_data="login")]
        ])
        await update.message.reply_text(
            "👋 Welcome!\nPlease sign up or log in to continue:",
            reply_markup=buttons
        )
        return MAIN_MENU

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    telegram_id = query.from_user.id
    data = query.data

    if data == "signup":
        await query.edit_message_text("👤 Please enter your desired username:")
        return SIGNUP_USERNAME

    elif data == "login":
        await query.edit_message_text("🔐 Please enter your username:")
        return LOGIN_USERNAME

    elif data == "search":
        await query.edit_message_text("🔍 Enter the product name to search:")
        return GET_QUERY

    elif data == "feedback":
        await query.edit_message_text("💬 Please type your feedback and press Enter:")
        return GET_FEEDBACK

    elif data == "exit":
        await query.edit_message_text("👋 Thank you for using our bot. Goodbye!")
        return ConversationHandler.END

async def handle_signup_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    username = update.message.text.strip()

    if is_username_taken(username):
        await update.message.reply_text("❗ This username is already taken. Please choose another one:")
        return SIGNUP_USERNAME

    register_user(telegram_id, username)
    await update.message.reply_text(
        f"✅ Registration complete: {username}\nYou can now search for products.",
        reply_markup=main_menu_buttons()
    )
    return MAIN_MENU

async def handle_login_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    username = update.message.text.strip()

    if not is_username_taken(username):
        await update.message.reply_text("❌ This user does not exist. Please sign up first.")
        return MAIN_MENU

    user_info = get_user_info(telegram_id)
    if user_info is None:
        await update.message.reply_text("❌ No registration found with this Telegram account. Please sign up.")
        return MAIN_MENU

    await update.message.reply_text(
        f"🔓 Logged in successfully: {username}",
        reply_markup=main_menu_buttons()
    )
    return MAIN_MENU

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    query = update.message.text.strip()

    user_info = get_user_info(telegram_id)
    if user_info is None:
        await update.message.reply_text("❌ Please log in first.")
        return MAIN_MENU

    is_vip = user_info.get("is_vip", False)
    search_count = user_info.get("search_count", 0)
    max_limit = 15 if is_vip else 3

    if search_count >= max_limit:
        await update.message.reply_text("🛑 You have reached your search limit.")
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
        await update.message.reply_text("😔 Sorry, no results found.")
        return MAIN_MENU

    products_by_site = defaultdict(list)
    for product in all_products:
        products_by_site[product["site"]].append(product)

    products_to_show = all_products if is_vip else [products[0] for products in products_by_site.values() if products]

    for product in products_to_show:
        formatted_price = convert_price_to_usd(product["price"])
        msg = (
            f"🌐 *{product['site']}*\n"
            f"📦 *Product*: {product['title']}\n"
            f"💰 *Price*: {formatted_price}\n"
            f"🔗 [Link]({product['link']})"
        )
        await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=False)

    increment_search_count(telegram_id)
    return MAIN_MENU

async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    feedback_text = update.message.text.strip()
    store_feedback(telegram_id, feedback_text)
    await update.message.reply_text("✅ Thank you for your feedback!", reply_markup=main_menu_buttons())
    return MAIN_MENU

if __name__ == "__main__":
    application = ApplicationBuilder().token("8051783595:AAENND4Ck3l7z1mao6WKxBYdrv2gskVmKzM").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(handle_callback)],
            SIGNUP_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_signup_username)],
            LOGIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login_username)],
            GET_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query)],
            GET_FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback)],
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    print("✅ Bot started... 🎈")
    application.run_polling()
