import asyncio
import logging
import logging.config

from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait

from config import Config
from database import db

# ✅ Tambahkan ini untuk web server dummy
from aiohttp import web
from plugins import web_server

# Setup logging
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

class Bot(Client):
    def __init__(self):
        super().__init__(
            Config.BOT_SESSION,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins={"root": "plugins"},
            workers=50
        )
        self.log = logging

    async def start(self):
        await super().start()

        # ✅ Start web server dummy untuk Koyeb health check
        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", port=80).start()

        me = await self.get_me()
        logging.info(f"{me.first_name} with for pyrogram v{__version__} (Layer {layer}) started on @{me.username}.")
        
        self.id = me.id
        self.username = me.username
        self.first_name = me.first_name
        self.set_parse_mode(ParseMode.DEFAULT)

        text = "**Bot Restarted !**"
        logging.info(text)

        success = failed = 0
        users = await db.get_all_frwd()
        async for user in users:
            chat_id = user['user_id']
            try:
                await self.send_message(chat_id, text)
                success += 1
            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
                await self.send_message(chat_id, text)
                success += 1
            except Exception:
                failed += 1

        if (success + failed) != 0:
            await db.rmve_frwd(all=True)
            logging.info(f"Restart message status: success={success}, failed={failed}")

    async def stop(self, *args):
        msg = f"@{self.username} stopped. Bye."
        await super().stop()
        logging.info(msg)

# ✅ Inisiasi & jalankan bot
app = Bot()
app.run()
