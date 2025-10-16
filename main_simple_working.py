#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIMPLE WORKING BOT - No ConversationHandler
Direct handlers, always responds
"""

import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from functions import (
    is_user_registered, register_user, get_user_info,
    increment_search_count, store_feedback, log_search_query,
    create_paypal_payment, get_available_searches
)
from search_script import fetch_amazon, filter_results
from config import BOT_TOKEN, CREDIT_PACKAGES, ADMIN_TELEGRAM_ID, ADMIN_BOT_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ============================================================================
# MENU
# ============================================================================

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Məhsul Axtar", callback_data="search")],
        [InlineKeyboardButton("💰 Kredit Al", callback_data="buy_credits")],
        [InlineKeyboardButton("💬 Rəy Yaz", callback_data="feedback")]
    ])

# ============================================================================
# START COMMAND
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple start - ALWAYS WORKS"""
    telegram_id = update.effective_user.id
    username = update.effective_user.username or f"user_{telegram_id}"
    
    # Auto-register
    if not is_user_registered(telegram_id):
        register_user(telegram_id, username)
    
    credits = get_available_searches(telegram_id)
    
    await update.message.reply_text(
        f"👋 *Xoş gəlmisiniz!*\n\n"
        f"💰 Kredit: {credits}\n\n"
        f"Seçim edin:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ============================================================================
# CALLBACK HANDLER
# ============================================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    telegram_id = query.from_user.id
    
    if data == "search":
        credits = get_available_searches(telegram_id)
        if credits <= 0:
            await query.edit_message_text(
                "❌ Kredit yoxdur!\n\n💰 Kredit almaq üçün düyməyə bas:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Kredit Al", callback_data="buy_credits")]])
            )
        else:
            context.user_data['waiting_for'] = 'search'
            await query.edit_message_text(f"🔍 Məhsul adı yazın:\n\n💰 Kredit: {credits}")
    
    elif data == "buy_credits":
        buttons = []
        for key, pkg in CREDIT_PACKAGES.items():
            buttons.append([InlineKeyboardButton(f"💳 {pkg['name']} - ${pkg['price']}", callback_data=f"buy_{key}")])
        buttons.append([InlineKeyboardButton("🔙 Geri", callback_data="back")])
        await query.edit_message_text("💰 Paket seçin:", reply_markup=InlineKeyboardMarkup(buttons))
    
    elif data.startswith("buy_"):
        pkg_key = data.replace("buy_", "")
        pkg = CREDIT_PACKAGES.get(pkg_key)
        if pkg:
            url = create_paypal_payment(telegram_id, pkg['price'], "credits", pkg['credits'], pkg['name'])
            if url:
                await query.edit_message_text(
                    f"💳 {pkg['name']}\n💰 ${pkg['price']}\n\n[Ödəniş et]({url})",
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text("❌ Xəta! Yenidən cəhd edin.")
    
    elif data == "feedback":
        context.user_data['waiting_for'] = 'feedback'
        await query.edit_message_text("💬 Rəyinizi yazın:")
    
    elif data == "back":
        await start(update, context)

# ============================================================================
# MESSAGE HANDLER
# ============================================================================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    telegram_id = update.message.from_user.id
    text = update.message.text.strip()
    
    waiting_for = context.user_data.get('waiting_for')
    
    # SEARCH
    if waiting_for == 'search':
        context.user_data['waiting_for'] = None
        
        credits = get_available_searches(telegram_id)
        if credits <= 0:
            await update.message.reply_text("❌ Kredit yoxdur!", reply_markup=main_menu())
            return
        
        await update.message.reply_text(f"🔍 Axtarılır: {text}...")
        
        # Search
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, fetch_amazon, text)
        
        if not results:
            await update.message.reply_text("😔 Nəticə tapılmadı.", reply_markup=main_menu())
            return
        
        # Save results
        context.user_data['search_results'] = results
        context.user_data['search_query'] = text
        
        # Show results
        filter_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Ucuz →", callback_data="filter_cheapest"), InlineKeyboardButton("💎 ← Bahalı", callback_data="filter_expensive")],
            [InlineKeyboardButton("🏆 Top 3", callback_data="filter_top3_cheap"), InlineKeyboardButton("🌟 Top 5", callback_data="filter_top5_cheap")],
            [InlineKeyboardButton("📊 Hamısı", callback_data="filter_all")],
            [InlineKeyboardButton("🔙 Menu", callback_data="back")]
        ])
        
        message = f"🔍 *{text}*\n🎯 Tapıldı: {len(results)} məhsul\n\n"
        
        for i, p in enumerate(results[:10], 1):
            message += f"{i}. 🌐 *{p['site']}*\n   📦 {p['title'][:60]}...\n   💰 *{p['price']}*\n   [🔗 Bax]({p['link']})\n\n"
        
        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=filter_buttons, disable_web_page_preview=True)
        
        increment_search_count(telegram_id)
        log_search_query(telegram_id, text)
    
    # FEEDBACK
    elif waiting_for == 'feedback':
        context.user_data['waiting_for'] = None
        
        store_feedback(telegram_id, text)
        
        # Send to admin
        try:
            admin_bot = Bot(ADMIN_BOT_TOKEN)
            await admin_bot.send_message(ADMIN_TELEGRAM_ID, f"💬 Feedback:\n{text}")
        except:
            pass
        
        await update.message.reply_text("✅ Təşəkkürlər!", reply_markup=main_menu())
    
    # Unknown
    else:
        await update.message.reply_text("Menyu seçin:", reply_markup=main_menu())

# ============================================================================
# FILTER HANDLER
# ============================================================================

async def filter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle filter buttons"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("filter_"):
        return
    
    filter_type = query.data.replace("filter_", "")
    results = context.user_data.get('search_results', [])
    search_query = context.user_data.get('search_query', '')
    
    if not results:
        await query.edit_message_text("❌ Nəticə yoxdur.", reply_markup=main_menu())
        return
    
    filtered = filter_results(results, filter_type)
    
    filter_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Ucuz →", callback_data="filter_cheapest"), InlineKeyboardButton("💎 ← Bahalı", callback_data="filter_expensive")],
        [InlineKeyboardButton("🏆 Top 3", callback_data="filter_top3_cheap"), InlineKeyboardButton("🌟 Top 5", callback_data="filter_top5_cheap")],
        [InlineKeyboardButton("📊 Hamısı", callback_data="filter_all")],
        [InlineKeyboardButton("🔙 Menu", callback_data="back")]
    ])
    
    message = f"🔍 *{search_query}*\n🎯 Göstərilir: {len(filtered)} məhsul\n\n"
    
    for i, p in enumerate(filtered[:10], 1):
        message += f"{i}. 🌐 *{p['site']}*\n   📦 {p['title'][:60]}...\n   💰 *{p['price']}*\n   [🔗 Bax]({p['link']})\n\n"
    
    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=filter_buttons, disable_web_page_preview=True)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(filter_handler, pattern="^filter_"))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("✅ Simple bot starting...")
    print("Bot həmişə /start-a cavab verəcək!")
    app.run_polling(drop_pending_updates=True)

