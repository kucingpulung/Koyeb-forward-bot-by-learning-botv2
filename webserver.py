# Webserver untuk Uptime Robot / Koyeb

from aiohttp import web

# Fungsi respons saat homepage diakses
async def handle(request):
    print("✅ Ping dari UptimeRobot diterima.")
    return web.Response(text="✅ Bot aktif dan berjalan!")

# Fungsi utama webserver
async def start_webserver():
    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 80)  # GANTI ke port 80 agar bisa diakses UptimeRobot
    await site.start()
    print("🌐 Web server aktif di http://localhost:80/")
