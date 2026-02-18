import os
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

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Render service URL

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
telegram_app = Application.builder().token(BOT_TOKEN).build()

user_data_store = {}


# ------------------ BOT HANDLERS ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data_store[user_id] = {}

    await update.message.reply_text(
        "🎓 Training Registration\n\n"
        "1️⃣ Pay the registration fee.\n"
        "2️⃣ Send your FULL NAME.\n"
        "3️⃣ Send your PHONE NUMBER.\n"
        "4️⃣ Send a PHOTO of your payment receipt.\n\n"
        "Please send your FULL NAME now."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id not in user_data_store:
        await update.message.reply_text("Please press /start first.")
        return

    if "name" not in user_data_store[user_id]:
        user_data_store[user_id]["name"] = text
        await update.message.reply_text("✅ Name received.\nNow send your PHONE NUMBER.")
        return

    if "phone" not in user_data_store[user_id]:
        user_data_store[user_id]["phone"] = text
        await update.message.reply_text("✅ Phone received.\nNow send a PHOTO of your receipt.")
        return


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in user_data_store:
        return

    if "name" not in user_data_store[user_id] or "phone" not in user_data_store[user_id]:
        await update.message.reply_text("Please send name and phone first.")
        return

    name = user_data_store[user_id]["name"]
    phone = user_data_store[user_id]["phone"]
    photo = update.message.photo[-1]

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📥 New Registration\n\n👤 Name: {name}\n📞 Phone: {phone}\n🆔 User ID: {user_id}"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo.file_id,
        caption="🧾 Payment Receipt"
    )

    await update.message.reply_text("🎉 Registration submitted successfully!")

    del user_data_store[user_id]


# Add handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))


# ------------------ FLASK ROUTES ------------------

@app.route("/")
def home():
    return "Bot is running!"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok"


# ------------------ STARTUP ------------------

if __name__ == "__main__":
    import asyncio

    async def setup():
        await telegram_app.initialize()
        await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")

    asyncio.run(setup())

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
