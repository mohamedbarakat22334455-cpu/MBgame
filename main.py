import os, sqlite3, random, asyncio, logging
from aiogram import Bot, Dispatcher, types
from aiohttp import web

# إعداد اللوجز عشان نشوف العطل فين لو حصل
logging.basicConfig(level=logging.INFO)

# --- [ الإعدادات - حط التوكن الجديد هنا ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- [ قاعدة البيانات ] ---
conn = sqlite3.connect('armageddon_v12.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
db = conn.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS players 
             (uid INTEGER PRIMARY KEY, gold INTEGER DEFAULT 100, hp INTEGER DEFAULT 100, lvl INTEGER DEFAULT 1)''')
conn.commit()

# --- [ واجهة اللعبة - Glassmorphism النيون ] ---
async def handle_index(request):
    html = """
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON</title>
        <style>
            body { 
                background: radial-gradient(circle, #1a1a1a 0%, #000 100%); 
                color: #FFD700; font-family: sans-serif; height: 100vh; margin: 0; 
                display: flex; justify-content: center; align-items: center;
            }
            .glass { 
                background: rgba(255, 215, 0, 0.03); backdrop-filter: blur(15px);
                border: 1px solid rgba(255, 215, 0, 0.3); border-radius: 30px; 
                padding: 25px; width: 320px; text-align: center;
                box-shadow: 0 0 30px rgba(255, 215, 0, 0.1);
            }
            .hp-bar { width: 100%; background: #222; height: 10px; border-radius: 5px; border: 1px solid #FFD700; margin: 15px 0; overflow: hidden; }
            .hp-fill { background: linear-gradient(90deg, #f00, #900); height: 100%; width: 100%; transition: 0.5s; }
            .btn { 
                background: linear-gradient(45deg, #FFD700, #B8860B); color: #000; 
                border: none; padding: 12px; width: 100%; border-radius: 12px; 
                font-weight: bold; cursor: pointer; margin: 10px 0;
            }
            #log { font-size: 0.8em; color: #fff; height: 40px; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="glass">
            <h1 style="text-shadow: 0 0 10px #FFD700;">⚔️ ARMAGEDDON</h1>
            <div style="display:flex; justify-content:space-between; font-weight:bold;">
                <span>🪙 <span id="gold">100</span></span>
                <span>🎖 <span id="lvl">1</span></span>
            </div>
            <div class="hp-bar"><div id="hp-bar" class="hp-fill"></div></div>
            <img src="https://img.icons8.com/plasticine/200/fire-dragon.png" style="height:150px; filter: drop-shadow(0 0 15px #FFD700);">
            <div id="log">الوحش مستني خبطتك!</div>
            <button class="btn" onclick="play('attack')">💥 هجوم ملكي</button>
            <button class="btn" style="background:#fff" onclick="play('gift')">🎁 مكافأة</button>
        </div>
        <script>
            async function play(t) {
                const r = await fetch(`/api/play?t=${t}`);
                const d = await r.json();
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

async def handle_api(request):
    t = request.query.get('t')
    db_c = conn.cursor()
    db_c.execute("SELECT * FROM players WHERE uid = 1") # تجريبي
    p = dict(db_c.fetchone() or {"gold": 100, "hp": 100, "lvl": 1})
    g, h, l = p['gold'], p['hp'], p['lvl']
    
    if t == 'attack':
        g += 25; h = max(0, h-10); msg = "💥 ضربة قوية! كسبت 25 ذهب."
    elif t == 'gift':
        g += 50; msg = "🎁 مبروك! مكافأة 50 ذهب."
    
    db_c.execute("INSERT OR REPLACE INTO players (uid, gold, hp, lvl) VALUES (1, ?, ?, ?)", (g, h, l))
    conn.commit()
    return web.json_response({'gold': g, 'hp': h, 'lvl': l, 'msg': msg})

# --- [ الرد الفوري ] ---
@dp.message_handler(commands=['start'])
async def start(m: types.Message):
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔱 دخول أرمجدون", web_app=types.WebAppInfo(url=WEB_URL)))
    await m.reply(f"أهلاً يا محارب **{m.from_user.first_name}** 🏆\n\nالبوت شغال دلوقتي وجاهز للرد فوراً. ادخل الساحة الذهبية من الزرار تحت!", reply_markup=kb)

# --- [ التشغيل ] ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/play', handle_api)
    
    loop = asyncio.get_event_loop()
    # تشغيل البوت كـ Task خلفي لضمان عدم توقفه
    loop.create_task(dp.start_polling())
    web.run_app(app, host='0.0.0.0', port=port)
