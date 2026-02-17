import subprocess
import os
import re
import time
import requests

def update_env(url):
    env_path = ".env"
    if not os.path.exists(env_path):
        return
    
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    with open(env_path, "w") as f:
        for line in lines:
            if line.startswith("WEBAPP_URL="):
                f.write(f"WEBAPP_URL={url}\n")
            else:
                f.write(line)
    print(f"✅ Updated .env with WEBAPP_URL: {url}")

def start_tunnel():
    print("🚀 Starting Cloudflare Tunnel for Telegram Film...")
    
    # Path to cloudflared.exe
    cf_path = os.path.join("..", "cloudflared.exe")
    if not os.path.exists(cf_path):
        cf_path = "cloudflared.exe" # Try local
    
    try:
        process = subprocess.Popen(
            [cf_path, "tunnel", "--url", "http://localhost:9999"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        tunnel_url = None
        for line in process.stdout:
            print(line, end="")
            # Look for the trycloudflare.com URL
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                tunnel_url = match.group(0)
                update_env(tunnel_url)
                print(f"\n✨ TUNNEL READY: {tunnel_url}")
                
                # Notify Backend and Bot
                try:
                    resp = requests.post("http://localhost:9999/api/admin/config/webapp-url", json={"url": tunnel_url}, timeout=5)
                    if resp.status_code == 200:
                        print("✅ Bot Menu Button updated automatically!")
                except Exception as e:
                    print(f"⚠️ Could not notify backend to update bot: {e} (Is the server running?)")
                
                print("Keep this script running to maintain the connection.\n")
                # We don't break, so the process keeps running
                
    except Exception as e:
        print(f"❌ Error starting tunnel: {e}")

if __name__ == "__main__":
    start_tunnel()
