import os, sqlite3, random, asyncio
from aiogram import Bot, Dispatcher, types
from aiohttp import web

# --- [ الإعدادات ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app" # رابط موقعك
WEBHOOK_PATH = f'/webhook/{API_TOKEN}'
WEBHOOK_URL = f"{WEB_URL}{WEBHOOK_PATH}"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- [ قاعدة البيانات ] ---
conn = sqlite3.connect('armageddon_v21.db', check_same_thread=False)
db = conn.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS players 
             (uid INTEGER PRIMARY KEY, gold INTEGER DEFAULT 100, lvl INTEGER DEFAULT 1)''')
conn.commit()

# --- [ واجهة اللعبة - نيون جولد + Glassmorphism ] ---
async def handle_index(request):
    html = """
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON</title>
        <style>
            body { background: #000; color: #FFD700; font-family: sans-serif; text-align: center; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .glass { background: rgba(255, 215, 0, 0.05); backdrop-filter: blur(10px); border: 2px solid #FFD700; border-radius: 25px; padding: 30px; width: 80%; max-width: 350px; box-shadow: 0 0 20px #FFD700; }
            .btn { background: linear-gradient(45deg, #FFD700, #B8860B); border: none; padding: 15px; width: 100%; border-radius: 12px; font-weight: bold; cursor: pointer; color: #000; margin-top: 15px; }
            .shake { animation: shake 0.2s; }
            @keyframes shake { 0% {transform: translate(0)} 25% {transform: translate(5px)} 50% {transform: translate(-5px)} 100% {transform: translate(0)} }
        </style>
    </head>
    <body>
        <div class="glass" id="card">
            <h1 style="text-shadow: 0 0 10px #FFD700;">🔱 ARMAGEDDON</h1>
            <p>🪙 ذهب: <span id="gold">100</span> | 🎖 مستوى: <span id="lvl">1</span></p>
            <img src="https://img.icons8.com/plasticine/200/fire-dragon.png" style="height:150px;">
            <div id="log" style="color:#fff; margin:10px 0; font-size:0.9em;">الوحش مستني خبطتك!</div>
            <button class="btn" onclick="play()">⚔️ هجوم نووي</button>
        </div>
        <script>
            async function play() {
                document.getElementById('card').classList.add('shake');
                setTimeout(()=> document.getElementById('card').classList.remove('shake'), 200);
                const res = await fetch('/api/play');
                const d = await res.json();
                document.getElementById('gold').innerText = d.gold;
                document.getElementById('lvl').innerText = d.lvl;
                document.getElementById('log').innerText = d.msg;
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def handle_api(request):
    return web.json_response({'gold': random.randint(100, 1000), 'lvl': 1, 'msg': "💥 ضربة قوية!"})

# --- [ استقبال رسائل البوت ] ---
async def webhook_handler(request):
    data = await request.json()
    update = types.Update.to_object(data)
    await dp.process_update(update)
    return web.Response(status=200)

@dp.message_handler(commands=['start'])
async def start(m: types.Message):
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔱 دخول اللعبة", web_app=types.WebAppInfo(url=WEB_URL)))
    await m.reply(f"🏆 أهلاً يا **محمد**\nالبوت شغال بنظام الـ Webhook السريع!", reply_markup=kb)

# --- [ إعداد الـ Webhook ] ---
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)

if __name__ == '__main__':
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/play', handle_api)
    app.router.add_post(WEBHOOK_PATH, webhook_handler)
    
    app.on_startup.append(on_startup)
    
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host='0.0.0.0', port=port)
