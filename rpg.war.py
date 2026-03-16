import sqlite3, random, asyncio, os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web

# --- [ الإعدادات - التوكن الجديد ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- [ قاعدة البيانات المتكاملة ] ---
conn = sqlite3.connect('armageddon_v8.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
db = conn.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS players 
             (uid INTEGER PRIMARY KEY, name TEXT, gold INTEGER DEFAULT 100, hp INTEGER DEFAULT 100, 
              lvl INTEGER DEFAULT 1, wins INTEGER DEFAULT 0)''')
conn.commit()

# --- [ واجهة اللعبة - تصميم النيون جولد ] ---
async def handle_index(request):
    html = """
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON PRO</title>
        <style>
            :root { --gold: #FFD700; --neon: #ffcc00; }
            body { background: #000; color: var(--gold); font-family: 'Cairo', sans-serif; text-align: center; margin: 0; overflow-x: hidden; }
            .container { padding: 20px; max-width: 500px; margin: auto; }
            .card { border: 2px solid var(--gold); border-radius: 25px; padding: 20px; background: rgba(255, 215, 0, 0.05); box-shadow: 0 0 30px rgba(255, 215, 0, 0.2); margin-bottom: 20px; }
            .stats-bar { display: flex; justify-content: space-around; font-weight: bold; margin-bottom: 15px; text-shadow: 0 0 10px var(--gold); }
            .progress-container { background: #222; border-radius: 10px; height: 12px; border: 1px solid var(--gold); margin: 8px 0; overflow: hidden; }
            .hp-fill { background: linear-gradient(90deg, #ff0000, #900); height: 100%; width: 100%; transition: 0.5s; }
            .btn { background: linear-gradient(45deg, var(--gold), #B8860B); color: #000; border: none; padding: 15px; width: 100%; border-radius: 12px; font-weight: bold; font-size: 1.1em; cursor: pointer; margin: 8px 0; transition: 0.2s; }
            .btn:hover { transform: scale(1.02); box-shadow: 0 0 15px var(--gold); }
            .monster-box { height: 180px; display: flex; align-items: center; justify-content: center; position: relative; }
            .monster-img { height: 150px; filter: drop-shadow(0 0 15px var(--gold)); animation: float 3s infinite ease-in-out; }
            @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-15px); } }
            #log { font-size: 0.9em; height: 45px; color: #fff; margin-top: 10px; }
            .leaderboard { font-size: 0.8em; text-align: left; background: rgba(255,255,255,0.05); border-radius: 10px; padding: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1 style="margin: 0 0 10px 0; letter-spacing: 2px;">🛡 ARMAGEDDON</h1>
                <div class="stats-bar">
                    <span>🩸 <span id="hp">100</span>%</span>
                    <span>🪙 <span id="gold">100</span></span>
                    <span>🎖 ليفل <span id="lvl">1</span></span>
                </div>
                <div class="progress-container"><div id="hp-bar" class="hp-fill"></div></div>
                <div class="monster-box"><img src="https://img.icons8.com/plasticine/200/fire-dragon.png" class="monster-img"></div>
                <div id="log">التحدي بدأ.. اضرب بكل قوتك!</div>
                <button class="btn" onclick="play('attack')">⚔️ هجوم نووي</button>
                <button class="btn" style="background: #fff;" onclick="play('heal')">🧪 استعادة صحة (50🪙)</button>
            </div>
            
            <div class="card leaderboard">
                <h3 style="text-align:center; margin:0 0 10px 0;">🏆 قائمة الأساطير</h3>
                <div id="top-players">جاري تحميل الترتيب...</div>
            </div>
        </div>

        <script>
            async function play(type) {
                const res = await fetch(`/api/play?type=${type}`);
                const d = await res.json();
                document.getElementById('hp').innerText = d.hp;
                document.getElementById('gold').innerText = d.gold;
                document.getElementById('lvl').innerText = d.lvl;
                document.getElementById('hp-bar').style.width = d.hp + "%";
                document.getElementById('log').innerText = d.msg;
                loadLeaderboard();
            }

            async function loadLeaderboard() {
                const res = await fetch('/api/top');
                const players = await res.json();
                let html = '';
                players.forEach((p, i) => {
                    html += `<div>${i+1}. ${p.name} - ليفل ${p.lvl} (🪙${p.gold})</div>`;
                });
                document.getElementById('top-players').innerHTML = html;
            }
            loadLeaderboard();
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

# --- [ API الخلفية المطور ] ---
async def handle_play(request):
    type = request.query.get('type')
    uid = 12345 # سيتم ربطه بـ التليجرام ID
    db_c = conn.cursor()
    
    db_c.execute("SELECT * FROM players WHERE uid = ?", (uid,))
    p = dict(db_c.fetchone() or {"name": "محارب", "gold": 100, "hp": 100, "lvl": 1})
    
    g, h, l = p['gold'], p['hp'], p['lvl']
    msg = ""

    if type == 'attack':
        dmg, earn = random.randint(5, 15), random.randint(10, 30) * l
        h, g = max(0, h - dmg), g + earn
        if random.random() < 0.1: l += 1; msg = "🌟 انفجار طاقة! ارتفع مستواك."
        else: msg = f"💥 ضربة قوية! كسبت {earn} ذهب."
    elif type == 'heal' and g >= 50:
        g, h = g - 50, 100
        msg = "🧪 تم استعادة طاقتك بالكامل!"
    elif type == 'heal':
        msg = "❌ ذهبك لا يكفي للعلاج."

    db_c.execute("INSERT OR REPLACE INTO players (uid, name, gold, hp, lvl) VALUES (?, ?, ?, ?, ?)", (uid, p['name'], g, h, l))
    conn.commit()
    return web.json_response({'gold': g, 'hp': h, 'lvl': l, 'msg': msg})

async def handle_top(request):
    db_c = conn.cursor()
    db_c.execute("SELECT name, gold, lvl FROM players ORDER BY lvl DESC, gold DESC LIMIT 5")
    return web.json_response([dict(row) for row in db_c.fetchall()])

# --- [ تشغيل السيرفر والبوت (الربط الصحيح) ] ---
app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/api/play', handle_play)
app.router.add_get('/api/top', handle_top)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    # تحديث اسم المستخدم في القاعدة
    db_c = conn.cursor()
    db_c.execute("INSERT OR IGNORE INTO players (uid, name) VALUES (?, ?)", (message.from_user.id, message.from_user.full_name))
    conn.commit()

    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🔱 دخول ساحة أرمجدون", web_app=types.WebAppInfo(url=WEB_URL))
    )
    await message.reply(f"مرحباً بك يا بطل! 🏆\n\nأنت الآن في **ARMAGEDDON**\nاضغط على الزر الذهبي لتبدأ الحرب وتتصدر القائمة.", reply_markup=kb, parse_mode="Markdown")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    loop = asyncio.get_event_loop()
    # تشغيل البوت في الخلفية
    loop.create_task(executor.start_polling(dp, skip_updates=True))
    # تشغيل الويب سيرفر
    web.run_app(app, host='0.0.0.0', port=port)
