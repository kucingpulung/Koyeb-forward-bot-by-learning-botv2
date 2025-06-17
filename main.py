from bot import Bot
import asyncio
from webserver import start_webserver
from pyrogram import idle

app = Bot()

async def start_all():
    await app.start()
    print("🤖 Bot telah berjalan...")
    await start_webserver()  # Mulai webserver (port 80)
    print("🌐 Webserver aktif.")
    await idle()  # Tetap aktif hingga dihentikan
    await app.stop()
    print("❌ Bot dihentikan.")

if __name__ == "__main__":
    try:
        asyncio.run(start_all())
    except (KeyboardInterrupt, SystemExit):
        print("🔻 Proses dihentikan.")
