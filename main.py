from bot import Bot
import asyncio
from webserver import start_webserver
from pyrogram import idle

app = Bot()

async def start_bot():
    await app.start()
    print("🤖 Bot telah berjalan...")
    await idle()
    await app.stop()
    print("❌ Bot dihentikan.")

async def main():
    await asyncio.gather(
        start_webserver(),  # Jalan webserver
        start_bot()         # Jalan bot
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🔻 Proses dihentikan.")
