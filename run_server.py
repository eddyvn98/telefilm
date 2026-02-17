import uvicorn
import os
from backend.main import app

if __name__ == "__main__":
    print("🚀 Starting Telegram Film Server on Port 9999...")
    uvicorn.run(app, host="127.0.0.1", port=9999, log_level="debug")
