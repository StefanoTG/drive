import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import asyncio
import requests

# Load configuration from config.json
CONFIG_FILE = 'config.json'

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as config_file:
        config = json.load(config_file)
    BOT_TOKEN = config.get("bot_token")
    ADMIN_IDS = config.get("admin_ids", [])
    SERVICE_ACCOUNT_FILE = config.get("json_path")  # Path to the service account file
else:
    print(f"Configuration file {CONFIG_FILE} not found. Please run the setup script.")
    exit(1)

# Google Drive API setup
SCOPES = ['https://www.googleapis.com/auth/drive.file']

try:
    # Ensure the path is correct and the file exists
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"Service account file not found at: {SERVICE_ACCOUNT_FILE}")
        exit(1)
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
except Exception as e:
    print(f"Error loading service account credentials: {e}")
    exit(1)

service = build('drive', 'v3', credentials=creds)
bot_token = config.get('bot_token')

# File and URL management
SUBSCRIPTIONS_FILE = 'subscriptions.json'
pending_removal = {}  # To track which user is in the process of removing a subscription

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

# Function to get the user's preferred language or fallback to English
def get_translation(user_id, key):
    return translations['en'].get(key, key)

# Function to load saved v2ray subscriptions
def load_subscriptions():
    """Load the list of saved v2ray subscription URLs and file IDs."""
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, 'r') as file:
            return json.load(file)
    return []

# Function to save v2ray subscriptions
def save_subscriptions(subscriptions):
    """Save the list of v2ray subscription URLs and file IDs."""
    with open(SUBSCRIPTIONS_FILE, 'w') as file:
        json.dump(subscriptions, file)

# Function to upload the v2ray subscription to Google Drive and get a unique URL
def upload_to_drive(file_path, mime_type):
    """Upload a file to Google Drive and return the file ID."""
    file_metadata = {'name': os.path.basename(file_path)}
    media = MediaFileUpload(file_path, mimetype=mime_type)

    # Create a new file on Google Drive
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')

    # Set file permissions for viewing (anyone can view)
    permission_view = {
        'type': 'anyone',
        'role': 'reader',
    }
    service.permissions().create(fileId=file_id, body=permission_view).execute()

    # Set file permissions for editing (for you only)
    permission_edit = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': YOUR_GOOGLE_EMAIL,
    }
    service.permissions().create(fileId=file_id, body=permission_edit, sendNotificationEmail=False).execute()

    return file_id

def update_drive_file(file_id, file_path, mime_type):
    """Update an existing file on Google Drive."""
    media = MediaFileUpload(file_path, mimetype=mime_type)
    service.files().update(fileId=file_id, media_body=media).execute()

async def start(update: Update, context):
    """Handle the /start command."""
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(get_translation(user_id, 'private_bot'))
        return

    # Define the inline keyboard buttons
    keyboard = [
        [InlineKeyboardButton("Create", callback_data='create'), InlineKeyboardButton("Remove", callback_data='remove')],
        [InlineKeyboardButton("Update", callback_data='update'), InlineKeyboardButton("List", callback_data='list')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send message with buttons
    await update.message.reply_text(get_translation(user_id, 'start'), reply_markup=reply_markup)

async def button(update: Update, context):
    """Handle button clicks from the inline keyboard."""
    query = update.callback_query
    user_id = query.from_user.id  # Fetch user ID for permission check
    await query.answer()

    if query.data == 'create':
        await query.message.reply_text("Please send the v2ray subscription URL.")
    elif query.data == 'remove':
        pending_removal[user_id] = True  # Set flag to indicate the user is removing a subscription
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

async def handle_v2ray_subscription(update: Update, context):
    """Handle v2ray subscription URL and upload to Google Drive."""
    user_id = update.message.from_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text(get_translation(user_id, 'private_bot'))
        return

    url = update.message.text

    if pending_removal.get(user_id):
        await remove_subscription(update, context, url)  # Handle removing the subscription
        pending_removal.pop(user_id, None)  # Clear the removal flag
    else:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            file_content = response.text

            # Save the v2ray subscription to a temporary file
            file_name = f'v2ray_subscription_{user_id}.txt'  # Unique file name for each user
            with open(file_name, 'w') as file:
                file.write(file_content)

            # Upload the file to Google Drive and get the unique URL
            file_id = upload_to_drive(file_name, 'text/plain')

            # Store the subscription URL and Google Drive file ID
            subscriptions = load_subscriptions()
            subscriptions.append({
                'url': url,
                'file_id': file_id
            })
            save_subscriptions(subscriptions)

            # Send the Google Drive link to the user
            file_url = f'https://drive.google.com/uc?export=download&id={file_id}'
            await update.message.reply_text(get_translation(user_id, 'v2ray_uploaded').format(file_url))

            # Remove the local file after upload
            os.remove(file_name)

        except requests.RequestException as e:
            await update.message.reply_text(get_translation(user_id, 'update_error').format(e))

async def list_subscriptions(update: Update, context):
    """List all saved v2ray subscriptions."""
    query = update.callback_query
    user_id = query.from_user.id

    if user_id not in ADMIN_IDS:
        await query.message.reply_text(get_translation(user_id, 'no_permission'))
        return

    subscriptions = load_subscriptions()

    if not subscriptions:
        await query.message.reply_text(get_translation(user_id, 'no_subscriptions'))
        return

    # Build the list of subscriptions to display
    subscriptions_text = "\n".join([f"URL: {sub['url']} | File ID: {sub['file_id']}" for sub in subscriptions])
    await query.message.reply_text(get_translation(user_id, 'list_subscriptions').format(subscriptions_text))

async def remove_subscription(update: Update, context, url_to_remove=None):
    """Remove a specific v2ray subscription by URL."""
    user_id = update.message.from_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text(get_translation(user_id, 'no_permission'))
        return

    if url_to_remove is None:
        await update.message.reply_text(get_translation(user_id, 'ask_for_url'))
        return

    subscriptions = load_subscriptions()

    for subscription in subscriptions:
        if subscription['url'] == url_to_remove:
            subscriptions.remove(subscription)
            save_subscriptions(subscriptions)
            await update.message.reply_text(get_translation(user_id, 'remove_success'))
            return

    await update.message.reply_text(get_translation(user_id, 'remove_failure'))

async def update_all_subscriptions(update: Update, context):
    """Update all v2ray subscriptions and replace the Google Drive files."""
    query = update.callback_query
    user_id = query.from_user.id

    if user_id not in ADMIN_IDS:
        await query.message.reply_text(get_translation(user_id, 'no_permission'))
        return

    subscriptions = load_subscriptions()

    if not subscriptions:
        await query.message.reply_text(get_translation(user_id, 'no_subscriptions'))
        return

    updated_files = []
    errors = []

    for subscription in subscriptions:
        url = subscription['url']
        file_id = subscription['file_id']
        try:
            response = requests.get(url)
            response.raise_for_status()
            file_content = response.text

            # Save updated content to a file and upload it to Google Drive
            file_name = f'v2ray_subscription_update_{user_id}.txt'
            with open(file_name, 'w') as file:
                file.write(file_content)

            # Update the existing Google Drive file
            update_drive_file(file_id, file_name, 'text/plain')

            # Track successfully updated files
            updated_files.append(url)

            # Remove the local file
            os.remove(file_name)

        except requests.RequestException as e:
            errors.append(f"Error updating {url}: {str(e)}")

    if updated_files:
        await query.message.reply_text(get_translation(user_id, 'update_success').format(len(updated_files)))
    if errors:
        await query.message.reply_text("\n".join(errors))

# Set up Telegram bot
async def main():
    """Set up and start the bot."""
    application = Application.builder().token(bot_token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_v2ray_subscription))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("remove_subscription", remove_subscription))
    application.add_handler(CommandHandler("list_subscriptions", list_subscriptions))

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
