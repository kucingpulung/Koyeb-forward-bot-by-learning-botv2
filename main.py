# Jishu Developer 
# Jangan Hapus Kredit 🥺
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Developer @JishuDeveloper

from bot import Bot
import asyncio
from webserver import start_webserver
from pyrogram import idle

app = Bot()

# Fungsi untuk menjalankan bot
async def bot_runner():
    await app.start()
    print("🤖 Bot telah berjalan...")
    await idle()
    await app.stop()
    print("🤖 Bot telah berhenti.")

# Fungsi utama untuk menjalankan bot dan webserver secara paralel
async def runner():
    await asyncio.gather(
        bot_runner(),
        start_webserver()
    )

if __name__ == "__main__":
    asyncio.run(runner())

# Jishu Developer 
# Jangan Hapus Kredit 🥺
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
