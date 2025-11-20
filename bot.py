import logging
import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

DATA_FILE = 'linked_channels.json'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"sources": [], "destination": None}
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"sources": [], "destination": None}

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logging.error(f"Saving error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🤖 Auto Forward Bot Active!\n\n"
        "Multiple source channels → one destination (No Forward Tag).\n\n"
        "✨ Commands:\n"
        "/link source <channel_id/username>\n"
        "/link destination <channel_id/username>\n"
        "/check - View current settings"
    )
    await update.message.reply_text(msg)

async def link_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage:\n/link source @channel\n/link destination -100xxxx")
        return

    action_type = context.args[0].lower()
    identifier = context.args[1]

    data = load_data()

    try:
        chat_info = await context.bot.get_chat(identifier)
        resolved_id = chat_info.id
        title = chat_info.title

        if action_type == 'source':
            if len(data['sources']) >= 5:
                await update.message.reply_text("❌ Max 5 sources allowed.")
                return

            if resolved_id in data['sources']:
                await update.message.reply_text("⚠️ Already added.")
                return

            data['sources'].append(resolved_id)
            save_data(data)
            await update.message.reply_text(f"Added Source: {title}")

        elif action_type == 'destination':
            data['destination'] = resolved_id
            save_data(data)
            await update.message.reply_text(f"Destination Set: {title}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def check_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(
        f"Sources: {data['sources']}\nDestination: {data['destination']}"
    )

async def auto_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post:
        return

    data = load_data()

    if update.channel_post.chat.id in data["sources"]:
        if not data["destination"]:
            return

        try:
            await context.bot.copy_message(
                chat_id=data["destination"],
                from_chat_id=update.channel_post.chat.id,
                message_id=update.channel_post.message_id
            )
        except Exception as e:
            logging.error(f"Forward Error: {e}")

if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("link", link_channel))
    application.add_handler(CommandHandler("check", check_settings))

    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, auto_forward))

    print("Bot Running…")
    application.run_polling()
