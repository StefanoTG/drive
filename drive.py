import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import asyncio
import requests

# Load configuration
CONFIG_FILE = 'config.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"{CONFIG_FILE} not found. Please run setup_and_run.py first.")
        exit(1)
    with open(CONFIG_FILE, 'r') as file:
        return json.load(file)

config = load_config()

# Admin user IDs and Google email address
ADMIN_IDS = config['admin_ids']
YOUR_GOOGLE_EMAIL = config['google_email']

# Set up Google Drive API
SERVICE_ACCOUNT_FILE = config['service_account_file']
SCOPES = ['https://www.googleapis.com/auth/drive.file']

creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=creds)

# File and URL management
SUBSCRIPTIONS_FILE = 'subscriptions.json'
pending_removal = {}

# Translations for messages
translations = {
    'en': {
        'start': "Choose command from below:",
        'private_bot': "Boty ulanmak tölegli, admin: @Old_Stefano",
        'v2ray_uploaded': "v2ray subscription file uploaded to Google Drive: {}",
        'update_success': "Updated {} v2ray subscriptions.",
        'update_error': "Failed to fetch the v2ray subscription from the URL. Error: {}",
        'no_subscriptions': "No v2ray subscriptions found to update.",
        'no_permission': "You do not have permission to use this command.",
        'list_subscriptions': "Here are the current v2ray subscriptions:\n{}",
        'remove_success': "Subscription removed successfully.",
        'remove_failure': "Subscription URL not found.",
        'ask_for_url': "Please send the URL of the subscription you want to remove."
    }
}

def get_translation(user_id, key):
    return translations['en'].get(key, key)

def load_subscriptions():
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, 'r') as file:
            return json.load(file)
    return []

def save_subscriptions(subscriptions):
    with open(SUBSCRIPTIONS_FILE, 'w') as file:
        json.dump(subscriptions, file)

def upload_to_drive(file_path, mime_type):
    file_metadata = {'name': os.path.basename(file_path)}
    media = MediaFileUpload(file_path, mimetype=mime_type)

    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')

    permission_view = {
        'type': 'anyone',
        'role': 'reader',
    }
    service.permissions().create(fileId=file_id, body=permission_view).execute()

    permission_edit = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': YOUR_GOOGLE_EMAIL,
    }
    service.permissions().create(fileId=file_id, body=permission_edit, sendNotificationEmail=False).execute()

    return file_id

async def start(update: Update, context):
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(get_translation(user_id, 'private_bot'))
        return

    keyboard = [
        [InlineKeyboardButton("Create", callback_data='create'), InlineKeyboardButton("Remove", callback_data='remove')],
        [InlineKeyboardButton("Update", callback_data='update'), InlineKeyboardButton("List", callback_data='list')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_translation(user_id, 'start'), reply_markup=reply_markup)

async def button(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'create':
        await query.message.reply_text("Please send the v2ray subscription URL.")
    elif query.data == 'remove':
        pending_removal[user_id] = True
        await query.message.reply_text(get_translation(user_id, 'ask_for_url'))
    elif query.data == 'update':
        if user_id in ADMIN_IDS:
            await update_all_subscriptions(update, context)
        else:
            await query.message.reply_text(get_translation(user_id, 'no_permission'))
    elif query.data == 'list':
        if user_id in ADMIN_IDS:
            await list_subscriptions(update, context)
        else:
            await query.message.reply_text(get_translation(user_id, 'no_permission'))

# More functions (update_all_subscriptions, handle_v2ray_subscription, etc.) follow...

# Set up Telegram bot
async def main():
    """Set up and start the bot."""
    application = Application.builder().token(config['bot_token']).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_v2ray_subscription))
    application.add_handler(CallbackQueryHandler(button))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
