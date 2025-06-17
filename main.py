# Jishu Developer 
# Don't Remove Credit 🥺
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
    await start_webserver()
    await idle()
    await app.stop()

asyncio.run(main())






# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
