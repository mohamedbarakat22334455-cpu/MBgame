import os, sqlite3, random, asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from aiohttp import web

# --- [ الإعدادات ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app" # رابط Railway بتاعك

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- [ قاعدة البيانات ] ---
conn = sqlite3.connect('armageddon_v10.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
db = conn.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS players 
             (uid INTEGER PRIMARY KEY, gold INTEGER DEFAULT 100, hp INTEGER DEFAULT 100, lvl INTEGER DEFAULT 1)''')
conn.commit()

# --- [ واجهة اللعبة - نيون جولد ] ---
async def handle_game(request):
    html = """
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON</title>
        <style>
            body { background: #000; color: #FFD700; font-family: sans-serif; text-align: center; margin: 0; padding: 20px; }
            .card { border: 2px solid #FFD700; border-radius: 20px; padding: 20px; background: rgba(255, 215, 0, 0.05); box-shadow: 0 0 20px #FFD700; }
            .btn { background: linear-gradient(45deg, #FFD700, #B8860B); color: #000; border: none; padding: 15px; width: 100%; border-radius: 10px; font-weight: bold; cursor: pointer; margin-top: 10px; }
            .hp-bar { width: 100%; background: #333; height: 15px; border-radius: 10px; margin: 10px 0; border: 1px solid #FFD700; overflow: hidden; }
            .hp-fill { background: red; height: 100%; width: 100%; transition: 0.3s; }
            #log { height: 40px; color: #fff; font-size: 0.9em; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🛡 ARMAGEDDON</h1>
            <div style="display:flex; justify-content:space-around;">
                <span>🪙 ذهب: <span id="gold">100</span></span>
                <span>🎖 ليفل: <span id="lvl">1</span></span>
            </div>
            <div class="hp-bar"><div id="hp-bar" class="hp-fill"></div></div>
            <img src="https://img.icons8.com/plasticine/200/dragon.png" style="height:150px;">
            <div id="log">الوحش في انتظارك يا بطل!</div>
            <button class="btn" onclick="play('attack')">⚔️ هجوم نووي</button>
            <button class="btn" style="background:#fff" onclick="play('gift')">🎁 مكافأة سريعة</button>
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
    t = request.query.get('type')
    db_c = conn.cursor()
    db_c.execute("SELECT * FROM players WHERE uid = 12345")
    p = dict(db_c.fetchone() or {"gold": 100, "hp": 100, "lvl": 1})
    g, h, l = p['gold'], p['hp'], p['lvl']
    
    if t == 'attack':
        earn = random.randint(10, 30); g += earn; h = max(0, h-10)
        msg = f"💥 ضربت الوحش وكسبت {earn} ذهب!"
    elif t == 'gift':
        bonus = 50; g += bonus; msg = "🎁 خد 50 ذهب هدية مني ليك!"
    
    db_c.execute("INSERT OR REPLACE INTO players (uid, gold, hp, lvl) VALUES (12345, ?, ?, ?)", (g, h, l))
    conn.commit()
    return web.json_response({'gold': g, 'hp': h, 'lvl': l, 'msg': msg})

# --- [ أوامر البوت ] ---
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🔱 ابدأ الحرب", web_app=types.WebAppInfo(url=WEB_URL))
    )
    await message.reply(f"🏆 أهلاً بك يا محارب **{message.from_user.first_name}**\n\nأنا شغال دلوقت وجاهز.. دوس على الزرار وادخل الساحة!", reply_markup=kb)

# --- [ التشغيل المتوازي ] ---
async def on_startup(app):
    await bot.set_webhook(WEB_URL + '/webhook')

async def on_shutdown(app):
    await bot.delete_webhook()

if __name__ == '__main__':
    app = web.Application()
    app.router.add_get('/', handle_game)
    app.router.add_get('/api/play', handle_play)
    
    # السر هنا: تشغيل البوت والويب سيرفر في Loop واحد
    port = int(os.environ.get("PORT", 8080))
    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling()) # تشغيل البوت كـ Task خلفي
    web.run_app(app, host='0.0.0.0', port=port)
