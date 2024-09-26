import os
import json
import subprocess

CONFIG_FILE = 'config.json'

def create_config():
    config_template = {
        "bot_token": "YOUR_BOT_TOKEN_HERE",
        "admin_ids": [123456789, 2128987754],
        "service_account_file": "/path/to/your/service_account.json",
        "google_email": "your-email@example.com"
    }
    
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as file:
            json.dump(config_template, file, indent=4)
        print(f"Configuration file '{CONFIG_FILE}' created. Please fill in your details.")

def install_requirements():
    if os.path.exists('requirements.txt'):
        subprocess.run(["pip3", "install", "-r", "requirements.txt"], check=True)
    else:
        print("requirements.txt not found.")

def run_script():
    subprocess.run(["python3", "drive.py"])

if __name__ == "__main__":
    create_config()
    install_requirements()
    run_script()
