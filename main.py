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

async def main():
    await app.start()
    print("🤖 Bot telah berjalan...")

    # Jalankan webserver sebagai task terpisah
    asyncio.create_task(start_webserver())

    await idle()  # Menunggu hingga bot dimatikan secara manual (CTRL+C atau stop signal)
    await app.stop()
    print("🤖 Bot telah berhenti.")

if __name__ == "__main__":
    asyncio.run(main())

# Jishu Developer 
# Jangan Hapus Kredit 🥺
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
