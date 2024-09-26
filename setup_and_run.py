# Inside configure_bot function in setup_and_run.py
def configure_bot():
    print("Please update your configuration details:")
    bot_token = input("Enter your Telegram Bot Token: ")
    admin_ids = input("Enter your Admin IDs (comma-separated): ").split(',')
    json_path = input("Enter path to your service account JSON file: ")

    # Verify the JSON file exists
    if not os.path.exists(json_path):
        print(f"Service account file not found at: {json_path}. Please ensure the path is correct.")
        exit(1)

    # Save the configuration
    config = {
        "bot_token": bot_token.strip(),
        "admin_ids": [int(admin_id.strip()) for admin_id in admin_ids if admin_id.strip().isdigit()],
        "json_path": json_path.strip()
    }

    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
    print("Configuration saved successfully.")
