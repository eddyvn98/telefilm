import logging
import os
import asyncio
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv

load_dotenv()

SPEED_TEST_URL = os.getenv("WEBAPP_URL", "https://google.com") # Placeholder, user needs to set this
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

import httpx

async def get_live_webapp_url():
    """Fetch the current WebApp URL from the backend API, or re-read .env."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:9999/api/admin/stats", timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                url = data.get("webapp_url")
                if url: return url
    except:
        pass
    
    # Fallback: Reload .env file to get the latest change from start_tunnel.py
    from dotenv import load_dotenv
    load_dotenv(override=True)
    return os.getenv("WEBAPP_URL", SPEED_TEST_URL)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Sends a message with a button to open the Web App.
    """
    url = await get_live_webapp_url()
    user = update.effective_user
    await update.message.reply_html(
        f"Hello {user.mention_html()}! \n\n"
        "Welcome to <b>Telegram Film</b>.\n"
        "Click the button below to start watching.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Open Cinema", web_app=WebAppInfo(url=url))]
        ])
    )
    
    # Update Menu Button for this chat
    await context.bot.set_chat_menu_button(
        chat_id=update.effective_chat.id,
        menu_button=MenuButtonWebApp(text="Open Cinema", web_app=WebAppInfo(url=url))
    )

async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hidden command to refresh the global Menu Button."""
    url = await get_live_webapp_url()
    await context.bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(text="🎬 Open Cinema", web_app=WebAppInfo(url=url))
    )
    await update.message.reply_text(f"✅ Bot Menu Button refreshed to: {url}")

async def post_init(application):
    """Set the Menu Button globally for the bot."""
    webapp_url = os.getenv("WEBAPP_URL")
    if webapp_url:
        await application.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="🎬 Open Cinema", web_app=WebAppInfo(url=webapp_url))
        )
        print(f"✅ Menu Button set to: {webapp_url}")

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not found in environment variables.")
        exit(1)
        
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    
    start_handler = CommandHandler('start', start)
    refresh_handler = CommandHandler('refresh', refresh)
    application.add_handler(start_handler)
    application.add_handler(refresh_handler)
    
    print("Bot is running...")
    application.run_polling()
