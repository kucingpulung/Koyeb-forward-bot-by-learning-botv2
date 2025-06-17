# Webserver untuk Uptime Robot / Koyeb

from aiohttp import web

# Fungsi respons saat homepage diakses
async def handle(request):
    return web.Response(text="✅ Bot aktif dan berjalan!")

# Fungsi utama webserver
async def start_webserver():
    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("🌐 Web server aktif di http://localhost:8080/")
