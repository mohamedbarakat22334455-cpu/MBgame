import sqlite3, random, asyncio, os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web

# --- [ الإعدادات ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- [ قاعدة البيانات ] ---
conn = sqlite3.connect('armageddon_v9.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
db = conn.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS players 
             (uid INTEGER PRIMARY KEY, gold INTEGER DEFAULT 100, hp INTEGER DEFAULT 100, 
              lvl INTEGER DEFAULT 1, power INTEGER DEFAULT 20)''')
conn.commit()

# --- [ واجهة اللعبة - نيون جولد ] ---
async def handle_index(request):
    html = """
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON</title>
        <style>
            body { background: #000; color: #FFD700; font-family: sans-serif; text-align: center; margin: 0; }
            .card { border: 2px solid #FFD700; border-radius: 20px; padding: 20px; background: rgba(255, 215, 0, 0.05); box-shadow: 0 0 20px #FFD700; margin: 15px; }
            .btn { background: linear-gradient(45deg, #FFD700, #B8860B); color: #000; border: none; padding: 15px; width: 100%; border-radius: 10px; font-weight: bold; font-size: 1.1em; cursor: pointer; margin-top: 10px; }
            .hp-bar { width: 100%; background: #333; height: 15px; border-radius: 10px; margin: 10px 0; border: 1px solid #FFD700; overflow: hidden; }
            .hp-fill { background: red; height: 100%; width: 100%; transition: 0.3s; }
            .monster-img { height: 150px; filter: drop-shadow(0 0 10px #FFD700); margin: 15px 0; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🛡 ARMAGEDDON</h1>
            <div style="display:flex; justify-content:space-around; font-weight:bold;">
                <span>🪙 ذهب: <span id="gold">100</span></span>
                <span>🎖 مستوى: <span id="lvl">1</span></span>
            </div>
            <div class="hp-bar"><div id="hp-bar" class="hp-fill"></div></div>
            <img src="https://img.icons8.com/plasticine/200/fire-dragon.png" class="monster-img">
            <div id="log" style="height:35px; color:#fff">استعد للقتال!</div>
            <button class="btn" onclick="play('attack')">⚔️ هجوم مدمر</button>
            <button class="btn" style="background:#fff" onclick="play('gift')">🎁 هدية عشوائية</button>
        </div>
        <script>
            async function play(type) {
                const res = await fetch(`/api/play?type=${type}`);
                const d = await res.json();
                document.getElementById('gold').innerText = d.gold;
                document.getElementById('hp-bar').style.width = d.hp + "%";
                document.getElementById('lvl').innerText = d.lvl;
                document.getElementById('log').innerText = d.msg;
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def handle_play(request):
    type = request.query.get('type')
    uid = 12345
    db_c = conn.cursor()
    db_c.execute("SELECT * FROM players WHERE uid = ?", (uid,))
    p = dict(db_c.fetchone() or {"gold": 100, "hp": 100, "lvl": 1, "power": 20})
    
    g, h, l = p['gold'], p['hp'], p['lvl']
    msg = ""

    if type == 'attack':
        dmg, earn = random.randint(5, 15), random.randint(10, 30)
        h, g = max(0, h-dmg), g+earn
        msg = f"💥 ضربت الوحش وكسبت {earn} ذهب!"
    elif type == 'gift':
        bonus = random.randint(50, 100)
        g += bonus
        msg = f"🎁 مبروك يا بطل! لقيت {bonus} ذهب."

    db_c.execute("INSERT OR REPLACE INTO players (uid, gold, hp, lvl) VALUES (?, ?, ?, ?)", (uid, g, h, l))
    conn.commit()
    return web.json_response({'gold': g, 'hp': h, 'lvl': l, 'msg': msg})

# --- [ تشغيل البوت والسيرفر ] ---
app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/api/play', handle_play)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🔱 دخول اللعبة", web_app=types.WebAppInfo(url=WEB_URL))
    )
    await message.reply(f"🏆 أهلاً بك يا **محمد**\n\nاللعبة جاهزة دلوقت، اضغط تحت وابدأ الحرب!", reply_markup=kb)

async def on_startup(dp):
    print("--- البوت شغال دلوقت يا محمد ---")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    loop = asyncio.get_event_loop()
    # أهم سطرين عشان البوت يرد:
    loop.create_task(executor.start_polling(dp, skip_updates=True))
    web.run_app(app, host='0.0.0.0', port=port)
