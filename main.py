# main.py

from bot import Bot
from webserver import start_webserver
from pyrogram import idle
import asyncio

app = Bot()

async def main():
    await app.start()
    print("🤖 Bot telah berjalan...")

    # Jalankan webserver sebagai background task
    asyncio.create_task(start_webserver())

    await idle()  # Tunggu hingga bot dihentikan secara manual
    await app.stop()
    print("🤖 Bot telah berhenti.")

if __name__ == "__main__":
    asyncio.run(main())
