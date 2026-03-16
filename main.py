import os, sqlite3, random, asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web

# --- [ الإعدادات ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- [ قاعدة البيانات ] ---
conn = sqlite3.connect('armageddon_vFinal.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
db = conn.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS players 
             (uid INTEGER PRIMARY KEY, name TEXT, gold INTEGER DEFAULT 100, lvl INTEGER DEFAULT 1)''')
conn.commit()

# --- [ واجهة اللعبة - نيون جولد ] ---
async def handle_index(request):
    db.execute("SELECT name, gold FROM players ORDER BY gold DESC LIMIT 5")
    leaders = db.fetchall()
    leader_html = "".join([f"<li>{l['name'] if l['name'] else 'محارب'}: {l['gold']} 🪙</li>" for l in leaders])

    html = f"""
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ARMAGEDDON</title>
        <style>
            body {{ background: #000; color: #FFD700; font-family: sans-serif; text-align: center; padding: 20px; }}
            .glass {{ background: rgba(255, 215, 0, 0.05); backdrop-filter: blur(10px); border: 2px solid #FFD700; border-radius: 20px; padding: 20px; box-shadow: 0 0 15px #FFD700; }}
            .btn {{ background: linear-gradient(45deg, #FFD700, #B8860B); border: none; padding: 15px; width: 100%; border-radius: 10px; font-weight: bold; cursor: pointer; color: #000; margin-top: 15px; transition: 0.1s; }}
            .btn:active {{ transform: scale(0.95); }}
            .leaderboard {{ margin-top: 20px; padding-top: 15px; border-top: 1px solid #FFD700; text-align: right; }}
            ul {{ list-style: none; padding: 0; }}
            li {{ margin: 5px 0; border-bottom: 1px solid rgba(255,215,0,0.1); }}
        </style>
    </head>
    <body>
        <div class="glass">
            <h1 style="text-shadow: 0 0 10px #FFD700;">🛡 ARMAGEDDON</h1>
            <p>🪙 ذهب: <span id="gold">100</span> | 🎖 مستوى: <span id="lvl">1</span></p>
            <img src="https://img.icons8.com/plasticine/200/fire-dragon.png" style="height:140px;">
            <button class="btn" onclick="play()">⚔️ هجوم ملكي</button>
            <div class="leaderboard">
                <h3>🏆 المتصدرين:</h3>
                <ul>{leader_html}</ul>
            </div>
        </div>
        <script>
            async function play() {{
                const r = await fetch('/api/play');
                const d = await r.json();
                document.getElementById('gold').innerText = d.gold;
                document.getElementById('lvl').innerText = d.lvl;
            }}
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def handle_api(request):
    return web.json_response({'gold': random.randint(100, 5000), 'lvl': random.randint(1, 10)})

# --- [ أوامر البوت - نسخة aiogram 3 ] ---
@dp.message(Command("start"))
async def start(m: types.Message):
    db.execute("INSERT OR IGNORE INTO players (uid, name) VALUES (?, ?)", (m.from_user.id, m.from_user.first_name))
    conn.commit()
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔱 دخول اللعبة", web_app=types.WebAppInfo(url=WEB_URL))]
    ])
    await m.answer(f"🏆 أهلاً يا **{m.from_user.first_name}**\nالبوت رجع يشتغل بأقصى قوته! ادخل الساحة دلوقتي.", reply_markup=kb)

# --- [ التشغيل المتكامل ] ---
async def main():
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/play', handle_api)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    
    await site.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
