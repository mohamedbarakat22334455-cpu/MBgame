import os, sqlite3, random, asyncio, logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web

# --- [ الإعدادات ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- [ قاعدة البيانات ] ---
conn = sqlite3.connect('armageddon_pro.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
db = conn.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS players 
             (uid INTEGER PRIMARY KEY, name TEXT, gold INTEGER DEFAULT 100, 
              hp INTEGER DEFAULT 100, lvl INTEGER DEFAULT 1, exp INTEGER DEFAULT 0)''')
conn.commit()

# --- [ واجهة اللعبة - نيون جولد & مؤثرات ] ---
async def handle_index(request):
    db.execute("SELECT name, gold FROM players ORDER BY gold DESC LIMIT 5")
    leaders = db.fetchall()
    leader_html = "".join([f"<li>🏆 {l['name']}: {l['gold']} 🪙</li>" for l in leaders])

    html = f"""
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON</title>
        <style>
            body {{ background: #000; color: #FFD700; font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; padding: 20px; }}
            .card {{ background: rgba(255, 215, 0, 0.05); backdrop-filter: blur(15px); border: 2px solid #FFD700; border-radius: 25px; padding: 25px; box-shadow: 0 0 20px #FFD700; }}
            .stats {{ display: flex; justify-content: space-around; font-weight: bold; margin-bottom: 15px; }}
            .hp-bar {{ width: 100%; background: #222; height: 12px; border-radius: 10px; border: 1px solid #FFD700; overflow: hidden; margin: 10px 0; }}
            .hp-fill {{ background: linear-gradient(90deg, #f00, #900); height: 100%; width: 100%; transition: 0.3s; }}
            .btn {{ background: linear-gradient(45deg, #FFD700, #B8860B); border: none; padding: 15px; width: 100%; border-radius: 12px; font-weight: bold; cursor: pointer; color: #000; margin-top: 10px; box-shadow: 0 4px 10px rgba(255,215,0,0.3); }}
            .btn:active {{ transform: scale(0.98); }}
            .leaderboard {{ margin-top: 25px; text-align: right; border-top: 1px solid #FFD700; padding-top: 10px; font-size: 0.9em; }}
            ul {{ list-style: none; padding: 0; }}
            li {{ padding: 5px; border-bottom: 1px solid rgba(255,215,0,0.1); }}
            .monster {{ height: 150px; filter: drop-shadow(0 0 10px #FFD700); margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1 style="text-shadow: 0 0 10px #FFD700; margin: 0;">🛡 ARMAGEDDON</h1>
            <div class="stats">
                <span>🩸 <span id="hp">100</span>%</span>
                <span>🪙 <span id="gold">100</span></span>
                <span>🎖 Lvl <span id="lvl">1</span></span>
            </div>
            <div class="hp-bar"><div id="hp-bar" class="hp-fill"></div></div>
            <img src="https://img.icons8.com/plasticine/200/fire-dragon.png" class="monster" id="m-img">
            <div id="log" style="color:#fff; min-height:40px;">الوحش مستني ضربتك!</div>
            
            <button class="btn" onclick="play('attack')">⚔️ هجوم ملكي</button>
            <button class="btn" style="background:#333; color:#FFD700" onclick="play('heal')">🧪 جرعة شفاء</button>
            
            <div class="leaderboard">
                <h3>🏆 قائمة الشرف:</h3>
                <ul>{leader_html}</ul>
            </div>
        </div>
        <script>
            async function play(action) {{
                const res = await fetch(`/api/play?action=${{action}}`);
                const d = await res.json();
                document.getElementById('gold').innerText = d.gold;
                document.getElementById('hp').innerText = d.hp;
                document.getElementById('lvl').innerText = d.lvl;
                document.getElementById('hp-bar').style.width = d.hp + "%";
                document.getElementById('log').innerText = d.msg;
            }}
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def handle_api(request):
    action = request.query.get('action')
    # منطق اللعبة (تعديل الذهب و HP)
    gold = random.randint(200, 1000)
    hp = random.randint(50, 100)
    msg = "💥 ضربة قوية كسبت فيها ذهب!" if action == 'attack' else "🧪 تم استعادة الصحة!"
    return web.json_response({'gold': gold, 'hp': hp, 'lvl': 1, 'msg': msg})

# --- [ أوامر البوت ] ---
@dp.message(Command("start"))
async def start(m: types.Message):
    db.execute("INSERT OR IGNORE INTO players (uid, name) VALUES (?, ?)", (m.from_user.id, m.from_user.first_name))
    conn.commit()
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔱 دخول ساحة أرمجدون", web_app=types.WebAppInfo(url=WEB_URL))]
    ])
    await m.answer(f"🏆 أهلاً يا **{m.from_user.first_name}**\n\nاللعبة جاهزة ومتطورة! ادخل دلوقتي ونافس على قائمة المتصدرين.", reply_markup=kb)

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
