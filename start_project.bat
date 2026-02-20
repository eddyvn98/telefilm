@echo off
echo 🚀 Starting Telegram Film Project...

echo 1. Launching Backend Server...
start "Telegram Film Server" "run_server.bat"

echo 2. Launching Telegram Bot...
start "Telegram Film Bot" "run_bot.bat"

echo 3. Launching Cloudflare Tunnel...
start "Cloudflare Tunnel" cmd /k "python start_tunnel.py"

echo ✅ All services launched in separate windows!
timeout /t 3
