#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRODUCTION BOT - Always Running, Beautiful UI
"""

import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from functions import is_user_registered, register_user, get_user_info, increment_search_count, store_feedback, log_search_query, create_paypal_payment, get_available_searches
from search_script import fetch_amazon, filter_results
from config import BOT_TOKEN, CREDIT_PACKAGES, ADMIN_TELEGRAM_ID, ADMIN_BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)

# ============================================================================
# BEAUTIFUL MENUS
# ============================================================================

def main_menu():
    """Beautiful main menu"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Search Products", callback_data="search")],
        [InlineKeyboardButton("💳 Buy Credits", callback_data="buy_credits")],
        [InlineKeyboardButton("💬 Send Feedback", callback_data="feedback")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ])

def filter_menu():
    """Filter buttons"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Cheapest First", callback_data="filter_cheapest"),
            InlineKeyboardButton("💎 Most Expensive", callback_data="filter_expensive")
        ],
        [
            InlineKeyboardButton("🏆 Top 3 Deals", callback_data="filter_top3"),
            InlineKeyboardButton("⭐ Top 5 Deals", callback_data="filter_top5")
        ],
        [InlineKeyboardButton("📊 Show All", callback_data="filter_all")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
    ])

# ============================================================================
# START COMMAND
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - ALWAYS WORKS on any device"""
    telegram_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or f"User{telegram_id}"
    
    # Auto-register if new user
    if not is_user_registered(telegram_id):
        register_user(telegram_id, username)
        is_new = True
    else:
        is_new = False
    
    credits = get_available_searches(telegram_id)
    
    if is_new:
        welcome = (
            "🎉 *Welcome to Product Search Bot!*\n\n"
            "✨ You got *3 FREE searches* to start!\n\n"
            "🌐 *Search across:*\n"
            "   • Amazon\n"
            "   • eBay\n"
            "   • Walmart\n"
            "   • Best Buy\n"
            "   • Etsy\n"
            "   • Newegg\n\n"
            f"💰 *Your Credits:* {credits}\n\n"
            "👇 Choose an option below:"
        )
    else:
        welcome = (
            f"👋 *Welcome back, {username}!*\n\n"
            f"💰 *Your Credits:* {credits}\n\n"
            "🔍 Ready to search!\n\n"
            "👇 Choose an option:"
        )
    
    await update.message.reply_text(
        welcome,
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ============================================================================
# BUTTON HANDLER
# ============================================================================

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    telegram_id = query.from_user.id
    
    # SEARCH
    if data == "search":
        credits = get_available_searches(telegram_id)
        if credits <= 0:
            await query.edit_message_text(
                "❌ *No credits available!*\n\n"
                "💡 Buy credits to start searching:",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💳 Buy Credits", callback_data="buy_credits")]])
            )
        else:
            context.user_data['waiting_for'] = 'search'
            await query.edit_message_text(
                f"🔍 *Enter product name:*\n\n"
                f"💰 Available: {credits} credits\n\n"
                f"_Type the product you want to search..._",
                parse_mode="Markdown"
            )
    
    # BUY CREDITS
    elif data == "buy_credits":
        buttons = []
        for key, pkg in CREDIT_PACKAGES.items():
            btn_text = f"💳 {pkg['name']} - ${pkg['price']:.2f}"
            buttons.append([InlineKeyboardButton(btn_text, callback_data=f"package_{key}")])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="menu")])
        
        await query.edit_message_text(
            "💰 *Choose a Credit Package:*\n\n"
            "Select the package that suits you:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    # BUY PACKAGE
    elif data.startswith("package_"):
        pkg_key = data.replace("package_", "")
        pkg = CREDIT_PACKAGES.get(pkg_key)
        
        if pkg:
            payment_url = create_paypal_payment(
                telegram_id,
                pkg['price'],
                "credits",
                pkg['credits'],
                pkg['name']
            )
            
            if payment_url:
                await query.edit_message_text(
                    f"💳 *{pkg['name']}*\n\n"
                    f"💰 Price: ${pkg['price']:.2f}\n"
                    f"🔍 Credits: {pkg['credits']} searches\n\n"
                    f"[✅ Complete Payment]({payment_url})",
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text("❌ Payment error. Try again.", reply_markup=main_menu())
    
    # FEEDBACK
    elif data == "feedback":
        context.user_data['waiting_for'] = 'feedback'
        await query.edit_message_text(
            "💬 *Send Your Feedback:*\n\n"
            "_Type your message, suggestions, or report issues..._",
            parse_mode="Markdown"
        )
    
    # HELP
    elif data == "help":
        help_text = (
            "ℹ️ *Help & Information*\n\n"
            "🔍 *How to search:*\n"
            "1. Click 'Search Products'\n"
            "2. Enter product name\n"
            "3. Get results from 7 stores!\n\n"
            "💰 *Pricing:*\n"
            "• 1 Search = 1 Credit\n"
            "• New users get 3 FREE credits\n"
            "• Buy more credits anytime\n\n"
            "🌐 *Supported Stores:*\n"
            "Amazon • eBay • Walmart\n"
            "BestBuy • Etsy • Newegg\n\n"
            "💡 *Features:*\n"
            "• Filter by price\n"
            "• Direct product links\n"
            "• Real-time results"
        )
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=main_menu())
    
    # BACK TO MENU
    elif data == "menu":
        credits = get_available_searches(telegram_id)
        await query.edit_message_text(
            f"📱 *Main Menu*\n\n💰 Credits: {credits}",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    
    # FILTERS
    elif data.startswith("filter_"):
        filter_type = data.replace("filter_", "")
        
        # Map filter names
        filter_map = {
            "top3": "top3_cheap",
            "top5": "top5_cheap"
        }
        filter_type = filter_map.get(filter_type, filter_type)
        
        results = context.user_data.get('search_results', [])
        search_query = context.user_data.get('search_query', '')
        
        if not results:
            await query.edit_message_text("❌ No results to filter.", reply_markup=main_menu())
            return
        
        filtered = filter_results(results, filter_type)
        
        # Filter display names
        filter_names = {
            "all": "All Results",
            "cheapest": "Cheapest First",
            "expensive": "Most Expensive",
            "top3_cheap": "Top 3 Deals",
            "top5_cheap": "Top 5 Deals"
        }
        
        message = (
            f"🔍 *Search:* {search_query}\n"
            f"📊 *Filter:* {filter_names.get(filter_type, 'All')}\n"
            f"🎯 *Showing:* {len(filtered)} products\n\n"
        )
        
        for i, product in enumerate(filtered[:10], 1):
            message += (
                f"{i}. 🌐 *{product['site']}*\n"
                f"   📦 {product['title'][:55]}...\n"
                f"   💰 *Price:* {product['price']}\n"
                f"   [🔗 View Product]({product['link']})\n\n"
            )
        
        if len(filtered) > 10:
            message += f"_...and {len(filtered) - 10} more products_\n\n"
        
        message += "👇 _Choose filter:_"
        
        await query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=filter_menu(),
            disable_web_page_preview=True
        )

# ============================================================================
# MESSAGE HANDLER
# ============================================================================

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    telegram_id = update.message.from_user.id
    text = update.message.text.strip()
    
    waiting_for = context.user_data.get('waiting_for')
    
    # SEARCH
    if waiting_for == 'search':
        context.user_data['waiting_for'] = None
        
        credits = get_available_searches(telegram_id)
        if credits <= 0:
            await update.message.reply_text("❌ No credits!", reply_markup=main_menu())
            return
        
        await update.message.reply_text(f"🔍 *Searching for:* {text}\n⏳ Please wait...", parse_mode="Markdown")
        
        # Search using Google API
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, fetch_amazon, text)
        
        if not results:
            await update.message.reply_text("😔 *No results found.*\n\n💡 Try different keywords.", parse_mode="Markdown", reply_markup=main_menu())
            return
        
        # Save results for filtering
        context.user_data['search_results'] = results
        context.user_data['search_query'] = text
        
        # Display results
        message = (
            f"🔍 *Search:* {text}\n"
            f"🎯 *Found:* {len(results)} products\n\n"
        )
        
        for i, product in enumerate(results[:10], 1):
            message += (
                f"{i}. 🌐 *{product['site']}*\n"
                f"   📦 {product['title'][:55]}...\n"
                f"   💰 *Price:* {product['price']}\n"
                f"   [🔗 View Product]({product['link']})\n\n"
            )
        
        if len(results) > 10:
            message += f"_...and {len(results) - 10} more products_\n\n"
        
        message += "👇 _Use filters to sort:_"
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=filter_menu(),
            disable_web_page_preview=True
        )
        
        # Deduct credit
        increment_search_count(telegram_id)
        log_search_query(telegram_id, text)
        
        # Show remaining
        remaining = get_available_searches(telegram_id)
        await update.message.reply_text(f"✅ *Search complete!*\n💰 Remaining credits: {remaining}", parse_mode="Markdown")
    
    # FEEDBACK
    elif waiting_for == 'feedback':
        context.user_data['waiting_for'] = None
        
        username = update.message.from_user.username or "Unknown"
        first_name = update.message.from_user.first_name or "User"
        
        # Save to database
        store_feedback(telegram_id, text)
        
        # Send to admin
        try:
            admin_bot = Bot(ADMIN_BOT_TOKEN)
            await admin_bot.send_message(
                ADMIN_TELEGRAM_ID,
                f"💬 *New Feedback!*\n\n"
                f"👤 User: @{username}\n"
                f"🆔 ID: {telegram_id}\n"
                f"📝 Name: {first_name}\n\n"
                f"*Message:*\n{text}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Failed to send feedback: {e}")
        
        await update.message.reply_text(
            "✅ *Thank you for your feedback!*\n\n"
            "We appreciate your input.",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    
    # DEFAULT
    else:
        await update.message.reply_text(
            "📱 *Main Menu*\n\n"
            "Choose an option below:",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🤖 INDICOME BOT - PRODUCTION MODE")
    print("="*60)
    print("  ✅ Always-on mode activated")
    print("  🔄 Auto-restart on crash")
    print("  🌐 Multi-site product search")
    print("  💰 3 API failover system (300 queries/day)")
    print("="*60 + "\n")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    
    logging.info("🚀 Bot starting...")
    logging.info("📱 Listening for messages...")
    
    print("✅ Bot is running! Press Ctrl+C to stop.\n")
    
    # Run with auto-restart
    app.run_polling(drop_pending_updates=True)

