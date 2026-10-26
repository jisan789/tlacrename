import os
import sys
import asyncio
import uvicorn
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import API_ID, API_HASH, SESSION_STRING

async def cli_mode():
    print("Initializing Telegram client with provided session string...")
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print("Session is expired or unauthorized. Please generate a new session string.")
            return

        me = await client.get_me()
        print("Successfully logged in!")
        print(f"Name      : {me.first_name} {me.last_name or ''}".strip())
        print(f"Username  : @{me.username}" if me.username else "Username  : None")
        print(f"User ID   : {me.id}")
        print(f"Phone     : +{me.phone}" if me.phone else "Phone     : Hidden/None")
        print(f"Bot       : {'Yes' if me.bot else 'No'}")

    except Exception as e:
        print(f"An error occurred while connecting: {e}")
    finally:
        await client.disconnect()
        print("Client disconnected cleanly.")

def run_server():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))

    print("=====================================================")
    print(f"Starting Telegram Web Client on http://{host}:{port}")
    print(f"Local browser: http://localhost:{port}")
    print("=====================================================")
    uvicorn.run("app:app", host=host, port=port, log_level="info")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        asyncio.run(cli_mode())
    else:
        run_server()
