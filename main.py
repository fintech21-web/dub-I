import os
import asyncio
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------- ENV ---------------- #

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
WEBHOOK_URL = os.environ["WEBHOOK_URL"]

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

telegram_app = Application.builder().token(BOT_TOKEN).build()

# Create ONE global event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

user_data_store = {}

# ---------------- HANDLERS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store[user_id] = {}

    await update.message.reply_text(
        "🎓 Training Registration\n\n"
        "1️⃣ Pay registration fee\n"
        "2️⃣ Send FULL NAME\n"
        "3️⃣ Send PHONE NUMBER\n"
        "4️⃣ Send receipt photo\n\n"
        "Send your FULL NAME now."
    )

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Your Telegram ID is: {update.effective_user.id}"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_data_store:
        await update.message.reply_text("Press /start first.")
        return

    if "name" not in user_data_store[user_id]:
        user_data_store[user_id]["name"] = text
        await update.message.reply_text("Now send your PHONE NUMBER.")
        return

    if "phone" not in user_data_store[user_id]:
        user_data_store[user_id]["phone"] = text
        await update.message.reply_text("Now send receipt PHOTO.")
        return

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_data_store:
        return

    data = user_data_store[user_id]

    if "name" not in data or "phone" not in data:
        await update.message.reply_text("Send name and phone first.")
        return

    caption = (
        "📥 New Registration\n\n"
        f"👤 Name: {data['name']}\n"
        f"📞 Phone: {data['phone']}\n"
        f"🆔 Telegram ID: {user_id}"
    )

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=caption
        )

        await update.message.reply_text("✅ Registration submitted successfully.")
        del user_data_store[user_id]

    except Exception as e:
        logging.error(f"Error sending to admin: {e}")

# ---------------- ADD HANDLERS ---------------- #

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("id", get_id))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

# ---------------- WEBHOOK ---------------- #

@app.route("/")
def home():
    return "Bot is running"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    loop.run_until_complete(telegram_app.process_update(update))
    return "OK"

# ---------------- STARTUP ---------------- #

async def setup():
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")

loop.run_until_complete(setup())
