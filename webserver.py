from aiohttp import web

async def handle(request):
    print("✅ Ping dari UptimeRobot atau Koyeb diterima.")
    return web.Response(text="✅ Bot aktif dan berjalan!")

async def start_webserver():
    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=80)
    await site.start()
    print("🌐 Web server aktif di http://localhost:80/")
