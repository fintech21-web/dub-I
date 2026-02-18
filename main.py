import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Load secure environment variables
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Temporary memory storage
user_data_store = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    user_data_store[user_id] = {}

    await update.message.reply_text(
        "🎓 *Training Registration*\n\n"
        "To complete your registration:\n\n"
        "1️⃣ Pay the registration fee.\n"
        "2️⃣ Send your FULL NAME.\n"
        "3️⃣ Send your PHONE NUMBER.\n"
        "4️⃣ Send a PHOTO of your payment receipt.\n\n"
        "Please send your FULL NAME now.",
        parse_mode="Markdown"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id not in user_data_store:
        await update.message.reply_text("Please press /start first.")
        return

    # Save Name
    if "name" not in user_data_store[user_id]:
        user_data_store[user_id]["name"] = text
        await update.message.reply_text(
            "✅ Name received.\nNow send your PHONE NUMBER."
        )
        return

    # Save Phone
    if "phone" not in user_data_store[user_id]:
        user_data_store[user_id]["phone"] = text
        await update.message.reply_text(
            "✅ Phone received.\nNow send a PHOTO of your payment receipt."
        )
        return


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in user_data_store:
        await update.message.reply_text("Please press /start first.")
        return

    if "name" not in user_data_store[user_id] or "phone" not in user_data_store[user_id]:
        await update.message.reply_text("Please send your name and phone first.")
        return

    photo = update.message.photo[-1]
    name = user_data_store[user_id]["name"]
    phone = user_data_store[user_id]["phone"]

    # Send registration details to admin
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "📥 *New Trainee Registration*\n\n"
            f"👤 Name: {name}\n"
            f"📞 Phone: {phone}\n"
            f"🆔 User ID: {user_id}"
        ),
        parse_mode="Markdown"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo.file_id,
        caption="🧾 Payment Receipt"
    )

    await update.message.reply_text(
        "🎉 Registration submitted successfully!\n"
        "Please wait for admin confirmation."
    )

    del user_data_store[user_id]


def main():
    if not TOKEN or not ADMIN_ID:
        raise ValueError("BOT_TOKEN or ADMIN_ID not set in environment variables.")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
