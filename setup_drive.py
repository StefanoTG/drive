import json

config_file = 'config.json'

def setup():
    print("Setting up your Drive Bot...")

    # Prompt for bot token
    bot_token = input("Enter your Telegram bot token: ")

    # Prompt for admin IDs
    admin_ids = input("Enter admin Telegram IDs (comma separated): ")
    admin_ids = [int(id.strip()) for id in admin_ids.split(',')]

    # Prompt for Google Service Account JSON file path
    service_account_file = input("Enter the path to your Google Service Account JSON file: ")

    # Save configuration to file
    config = {
        'bot_token': bot_token,
        'admin_ids': admin_ids,
        'service_account_file': service_account_file
    }

    with open(config_file, 'w') as file:
        json.dump(config, file)

    print(f"Configuration saved in {config_file}. You can now start the bot.")

if __name__ == '__main__':
    setup()
