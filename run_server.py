import uvicorn
from backend.main import app

if __name__ == "__main__":
    print("Starting Telegram Film Server on http://127.0.0.1:9999")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=9999,
        log_level="info",
        server_header=False,
    )
