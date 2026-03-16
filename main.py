import os, sqlite3, random, asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from aiohttp import web

# --- [ الإعدادات ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app" # رابط موقعك على ريلواي
WEBHOOK_PATH = f'/webhook/{API_TOKEN}'
WEBHOOK_URL = f"{WEB_URL}{WEBHOOK_PATH}"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- [ قاعدة البيانات ] ---
conn = sqlite3.connect('armageddon_vFinal.db', check_same_thread=False)
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
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ARMAGEDDON</title>
        <style>
            body { background: #000; color: #FFD700; font-family: sans-serif; text-align: center; padding: 20px; }
            .glass { background: rgba(255, 215, 0, 0.05); backdrop-filter: blur(10px); border: 1px solid #FFD700; border-radius: 20px; padding: 20px; }
            .btn { background: linear-gradient(45deg, #FFD700, #B8860B); border: none; padding: 15px; width: 100%; border-radius: 10px; font-weight: bold; cursor: pointer; color: #000; margin-top: 10px; }
            .hp-bar { width: 100%; background: #222; height: 12px; border-radius: 10px; border: 1px solid #FFD700; margin: 10px 0; overflow: hidden; }
            .hp-fill { background: red; height: 100%; width: 100%; transition: 0.3s; }
        </style>
    </head>
    <body>
        <div class="glass">
            <h1>🛡 ARMAGEDDON</h1>
            <div style="display:flex; justify-content:space-around;">
                <span>🪙 <span id="gold">100</span></span>
                <span>🎖 <span id="lvl">1</span></span>
            </div>
            <div class="hp-bar"><div id="hp-bar" class="hp-fill"></div></div>
            <img src="https://img.icons8.com/plasticine/200/fire-dragon.png" style="height:150px;">
            <div id="log" style="color:#fff; margin-top:10px;">اضرب الوحش الآن!</div>
            <button class="btn" onclick="play('attack')">⚔️ هجوم ملكي</button>
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
    # منطق اللعبة البسيط
    return web.json_response({'gold': 150, 'hp': 90, 'lvl': 1, 'msg': "💥 تم الهجوم!"})

# --- [ أوامر البوت ] ---
@dp.message_handler(commands=['start'])
async def start(m: types.Message):
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔱 دخول اللعبة", web_app=types.WebAppInfo(url=WEB_URL)))
    await m.reply(f"🏆 أهلاً بك يا بطل!\nالبوت شغال الآن بنظام الـ Webhook السريع.", reply_markup=kb)

# --- [ تشغيل الـ Webhook ] ---
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

if __name__ == '__main__':
    app = web.Application()
    app.router.add_get('/', handle_game)
    app.router.add_get('/api/play', handle_api)
    
    # ربط تليجرام بالـ Webhook
    app.router.add_post(WEBHOOK_PATH, lambda r: start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, request=r))
    
    port = int(os.environ.get("PORT", 8080))
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        host='0.0.0.0',
        port=port
    )
