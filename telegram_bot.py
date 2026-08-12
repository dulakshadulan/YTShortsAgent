"""
telegram_bot.py
Listens for messages containing a reel URL, runs the full pipeline,
and replies with the finished YouTube Shorts link.

Run with:
    python telegram_bot.py
"""

import os
import re
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

from main import run

load_dotenv()
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not found. Add it to your .env file.")

URL_PATTERN = re.compile(r"https?://\S+")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = URL_PATTERN.search(text)

    if not match:
        await update.message.reply_text("Send me an Instagram or Facebook reel link and I'll turn it into a Short.")
        return

    url = match.group(0)
    await update.message.reply_text(f"Got it. Processing:\n{url}\n\nThis usually takes a few minutes...")

    try:
        # Run the (blocking, synchronous) pipeline in a background thread
        # so it doesn't freeze the bot's ability to respond to other messages.
        video_id = await asyncio.to_thread(run, url)
        await update.message.reply_text(f"Done! https://youtube.com/shorts/{video_id}")
    except Exception as e:
        await update.message.reply_text(f"Something went wrong:\n{e}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()