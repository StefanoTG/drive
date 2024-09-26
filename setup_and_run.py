import os
import json
import subprocess

CONFIG_FILE = 'config.json'
DRIVE_SCRIPT = 'drive.py'

# Required dependencies
REQUIRED_PACKAGES = [
    "google-auth",
    "google-auth-oauthlib",
    "google-auth-httplib2",
    "google-api-python-client",
    "python-telegram-bot==21.5",
    "requests",
]

def install_packages():
    """Install the required packages using pip."""
    print("Installing required packages...")
    subprocess.check_call(["pip", "install"] + REQUIRED_PACKAGES)
    print("Packages installed successfully.")

def create_config():
    """Create the config.json file with user inputs."""
    print("Creating config.json file...")
    config = {}

    # Prompt the user for input
    config['bot_token'] = input("Enter your Telegram bot token: ")
    admin_ids = input("Enter admin user IDs (comma-separated): ")
    config['admin_ids'] = [int(id.strip()) for id in admin_ids.split(',')]
    config['service_account_file'] = input("Enter the path to your Google service account JSON file: ")

    # Write the configuration to the JSON file
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)
    print(f"Configuration saved to {CONFIG_FILE}.")

def run_drive_script():
    """Run the drive.py script."""
    print("Starting the bot...")
    subprocess.run(["python3", DRIVE_SCRIPT])

def main():
    """Main function to set up and run the bot."""
    # Check if config.json exists; if not, create it
    if not os.path.exists(CONFIG_FILE):
        create_config()
    
    # Install required packages
    install_packages()
    
    # Run the bot script
    run_drive_script()

if __name__ == '__main__':
    main()
