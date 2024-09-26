import os
import subprocess
import json

# URLs for the scripts
DRIVE_SCRIPT_URL = "https://raw.githubusercontent.com/StefanoTG/drive/main/drive.py"  # Ensure this URL is correct

# Step 1: Download drive.py
def download_script(url, filename):
    print(f"Downloading {filename}...")
    result = subprocess.run(["wget", url, "-O", filename], check=True)
    if result.returncode == 0 and os.path.exists(filename):
        print(f"{filename} downloaded successfully.")
    else:
        print(f"Failed to download {filename}. Please check the URL.")
        exit(1)

# Step 2: Install requirements
def install_requirements():
    print("Installing required packages...")
    subprocess.run(["pip3", "install", "-r", "requirements.txt"], check=True)

# Step 3: Prompt user for configurations
def configure_bot():
    print("Please update your configuration details:")
    bot_token = input("Enter your Telegram Bot Token: ")
    admin_ids = input("Enter your Admin IDs (comma-separated): ").split(',')
    json_path = input("Enter path to your service account JSON file: ")

    # Create a config file with user inputs
    config = {
        "bot_token": bot_token.strip(),
        "admin_ids": [int(admin_id.strip()) for admin_id in admin_ids],
        "json_path": json_path.strip()
    }

    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
    print("Configuration saved successfully.")

# Step 4: Run the bot
def run_bot():
    print("Starting the bot...")
    if os.path.exists("drive.py"):
        subprocess.run(["python3", "drive.py"])
    else:
        print("Error: drive.py file not found. Please check the download step.")

if __name__ == "__main__":
    download_script(DRIVE_SCRIPT_URL, "drive.py")
    install_requirements()
    configure_bot()
    run_bot()
