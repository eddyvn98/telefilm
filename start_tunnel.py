import subprocess
import os
import re
import requests
from dotenv import load_dotenv

def update_env(url):
    env_path = ".env"
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated = False
    with open(env_path, "w", encoding="utf-8") as f:
        for line in lines:
            if line.startswith("WEBAPP_URL="):
                f.write(f"WEBAPP_URL={url}\n")
                updated = True
            else:
                f.write(line)
        if not updated:
            f.write(f"WEBAPP_URL={url}\n")
    print(f"✅ Updated .env with WEBAPP_URL: {url}")

def update_bot_menu(url):
    load_dotenv(override=True)
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("⚠️ BOT_TOKEN not configured; skipped menu-button update.")
        return
    endpoint = f"https://api.telegram.org/bot{bot_token}/setChatMenuButton"
    payload = {
        "menu_button": {
            "type": "web_app",
            "text": "🎬 Open Cinema",
            "web_app": {"url": url},
        }
    }
    response = requests.post(endpoint, json=payload, timeout=10)
    response.raise_for_status()
    print("✅ Telegram bot menu button updated automatically!")

def start_tunnel():
    print("🚀 Starting Cloudflare Tunnel for Telegram Film...")

    cf_path = os.path.join("..", "cloudflared.exe")
    if not os.path.exists(cf_path):
        cf_path = "cloudflared.exe"

    try:
        process = subprocess.Popen(
            [cf_path, "tunnel", "--url", "http://localhost:9999"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            print(line, end="")
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                tunnel_url = match.group(0)
                update_env(tunnel_url)
                print(f"\n✨ TUNNEL READY: {tunnel_url}")
                try:
                    update_bot_menu(tunnel_url)
                except Exception as exc:
                    print(f"⚠️ Could not update Telegram menu button: {exc}")
                print("Keep this script running to maintain the connection.\n")

    except Exception as exc:
        print(f"❌ Error starting tunnel: {exc}")

if __name__ == "__main__":
    start_tunnel()
