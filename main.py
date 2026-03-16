import os, sqlite3, random, asyncio, logging
from aiogram import Bot, Dispatcher, types
from aiohttp import web

# إعداد اللوجز لمراقبة أي خطأ
logging.basicConfig(level=logging.INFO)

# --- [ الإعدادات ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- [ قاعدة البيانات ] ---
conn = sqlite3.connect('armageddon_v20.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
db = conn.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS players 
             (uid INTEGER PRIMARY KEY, gold INTEGER DEFAULT 100, hp INTEGER DEFAULT 100, 
              lvl INTEGER DEFAULT 1, exp INTEGER DEFAULT 0, weapon_id INTEGER DEFAULT 0)''')
conn.commit()

# داتا اللعبة
WEAPONS = [
    {"name": "قبضة اليد", "pwr": 10, "price": 0},
    {"name": "خنجر النيون", "pwr": 50, "price": 300},
    {"name": "سيف الغضب", "pwr": 150, "price": 1200}
]

# --- [ واجهة اللعبة - نيون جولد + مؤثرات بصرية ] ---
async def handle_index(request):
    html = """
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON GOLD</title>
        <style>
            body { 
                background: #000; color: #FFD700; font-family: 'Segoe UI', sans-serif; 
                margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh;
                overflow: hidden;
            }
            .glass-card { 
                background: rgba(255, 215, 0, 0.05); backdrop-filter: blur(15px);
                border: 2px solid #FFD700; border-radius: 30px; padding: 25px;
                width: 85%; max-width: 380px; text-align: center;
                box-shadow: 0 0 25px rgba(255, 215, 0, 0.2);
                transition: transform 0.1s;
            }
            .neon-btn { 
                background: linear-gradient(45deg, #FFD700, #B8860B); border: none; 
                padding: 15px; width: 100%; border-radius: 15px; font-weight: bold; 
                cursor: pointer; color: #000; margin: 10px 0;
                box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
            }
            .hp-bar { width: 100%; background: #222; height: 10px; border-radius: 10px; border: 1px solid #FFD700; overflow: hidden; margin: 15px 0; }
            .hp-fill { background: linear-gradient(90deg, #ff0000, #900); height: 100%; width: 100%; transition: 0.3s; }
            .shake { animation: shake 0.2s; }
            @keyframes shake {
                0% { transform: translate(1px, 1px) rotate(0deg); }
                20% { transform: translate(-3px, 0px) rotate(-1deg); }
                50% { transform: translate(-1px, 2px) rotate(1deg); }
                100% { transform: translate(0px, 0px) rotate(0deg); }
            }
            .monster { height: 160px; filter: drop-shadow(0 0 10px #FFD700); margin: 15px 0; }
        </style>
    </head>
    <body>
        <div class="glass-card" id="card">
            <h2 style="text-shadow: 0 0 10px #FFD700;">🔱 ARMAGEDDON</h2>
            <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:0.9em;">
                <span>🪙 <span id="gold">100</span></span>
                <span>🎖 lvl <span id="lvl">1</span></span>
            </div>
            <div class="hp-bar"><div id="hp-bar" class="hp-fill"></div></div>
            <img src="https://img.icons8.com/plasticine/200/fire-dragon.png" class="monster" id="monster">
            <div id="log" style="font-size:0.8em; min-height:30px; color:#fff;">الوحش في انتظارك!</div>
            <button class="neon-btn" onclick="attack()">⚔️ هجوم نووي</button>
            <button class="neon-btn" style="background:#333; color:#FFD700" onclick="daily()">🎁 مكافأة يومية</button>
        </div>

        <script>
            async function attack() {
                // تأثير الاهتزاز عند الضربة
                const card = document.getElementById('card');
                card.classList.add('shake');
                setTimeout(() => card.classList.remove('shake'), 200);

                const res = await fetch('/api/play?type=attack');
                const d = await res.json();
                updateUI(d);
            }

            async function daily() {
                const res = await fetch('/api/play?type=daily');
                const d = await res.json();
                updateUI(d);
            }

            function updateUI(d) {
                document.getElementById('gold').innerText = d.gold;
                document.getElementById('lvl').innerText = d.lvl;
                document.getElementById('hp-bar').style.width = d.hp + "%";
                document.getElementById('log').innerText = d.msg;
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def handle_api(request):
    t = request.query.get('type')
    db_c = conn.cursor()
    db_c.execute("SELECT * FROM players WHERE uid = 1")
    p = dict(db_c.fetchone() or {"gold": 100, "hp": 100, "lvl": 1, "exp": 0, "weapon_id": 0})
    g, h, l, x, w_id = p['gold'], p['hp'], p['lvl'], p['exp'], p['weapon_id']

    if t == 'attack':
        earn = random.randint(20, 50); g += earn; h = max(0, h-10); x += 30
        if x >= 100: l += 1; x = 0; msg = f"🆙 مبروك! ليفل جديد {l}"
        else: msg = f"💥 كسبت {earn} ذهب من الهجوم!"
    elif t == 'daily':
        g += 100; msg = "🎁 استلمت 100 ذهب!"

    db_c.execute("INSERT OR REPLACE INTO players (uid, gold, hp, lvl, exp, weapon_id) VALUES (1, ?, ?, ?, ?, ?)", (g, h, l, x, w_id))
    conn.commit()
    return web.json_response({'gold': g, 'hp': h, 'lvl': l, 'msg': msg})

# --- [ أوامر البوت ] ---
@dp.message_handler(commands=['start'])
async def start_cmd(m: types.Message):
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔱 دخول اللعبة", web_app=types.WebAppInfo(url=WEB_URL)))
    await m.reply(f"🏆 أهلاً يا بطل!\nالبوت شغال دلوقتي.. اضغط تحت وابدأ اللعب فوراً.", reply_markup=kb)

# --- [ التشغيل ] ---
if __name__ == '__main__':
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/play', handle_api)
    
    port = int(os.environ.get("PORT", 8080))
    loop = asyncio.get_event_loop()
    # تشغيل البوت في الخلفية بشكل يضمن الاستجابة
    loop.create_task(dp.start_polling())
    web.run_app(app, host='0.0.0.0', port=port)
