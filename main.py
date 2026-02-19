import os
import asyncio
import logging
from flask import Flask, request
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
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

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ---------------- CONFIG ---------------- #

BANK_ACCOUNT_INFO = """
🏦 Bank Name: Commercial Bank
👤 Account Name: Training Center
🔢 Account Number: 1234567890

After payment, please send your receipt here.
"""

# ---------------- HANDLERS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 Register", callback_data="register")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎓 Welcome to Training Registration\n\n"
        "To complete your registration:\n"
        "1️⃣ Click Register\n"
        "2️⃣ Enter your details\n"
        "3️⃣ Pay the fee\n"
        "4️⃣ Send receipt\n\n"
        "Press the button below to begin.",
        reply_markup=reply_markup
    )


async def register_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.clear()
    context.user_data["step"] = "name"

    await query.message.reply_text("Please enter your FULL NAME.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")

    if step == "name":
        context.user_data["name"] = update.message.text
        context.user_data["step"] = "phone"
        await update.message.reply_text("Now enter your PHONE NUMBER.")
        return

    if step == "phone":
        context.user_data["phone"] = update.message.text
        context.user_data["step"] = "payment"

        await update.message.reply_text(
            "💳 Please send the registration fee to the account below:\n\n"
            + BANK_ACCOUNT_INFO
        )
        return


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")

    if step != "payment":
        return

    name = context.user_data.get("name")
    phone = context.user_data.get("phone")
    user_id = update.effective_user.id

    caption = (
        "📥 New Registration\n\n"
        f"👤 Name: {name}\n"
        f"📞 Phone: {phone}\n"
        f"🆔 Telegram ID: {user_id}"
    )

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=caption
        )

        await update.message.reply_text(
            "✅ Your registration has been successfully submitted.\n"
            "Our team will review your payment shortly."
        )

        context.user_data.clear()

    except Exception as e:
        logging.error(f"Error sending to admin: {e}")
        await update.message.reply_text("❌ Something went wrong. Please try again.")


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Your Telegram ID is: {update.effective_user.id}"
    )

# ---------------- ADD HANDLERS ---------------- #

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("id", get_id))
telegram_app.add_handler(CallbackQueryHandler(register_button, pattern="register"))
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
