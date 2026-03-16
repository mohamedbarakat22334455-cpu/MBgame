import sqlite3, random, asyncio, os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web

# --- [ الإعدادات ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- [ قاعدة البيانات المتكاملة ] ---
def init_db():
    conn = sqlite3.connect('armageddon_ultimate.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()
    db.execute('''CREATE TABLE IF NOT EXISTS players 
                 (uid INTEGER PRIMARY KEY, gold INTEGER DEFAULT 100, hp INTEGER DEFAULT 100, 
                  exp INTEGER DEFAULT 0, lvl INTEGER DEFAULT 1, w_id INTEGER DEFAULT 0)''')
    conn.commit()
    return conn

db_conn = init_db()

WEAPONS = [
    {"id": 0, "name": "قبضة اليد", "p": 10, "cost": 0},
    {"id": 1, "name": "خنجر حديدي", "p": 40, "cost": 200},
    {"id": 2, "name": "سيف البرق", "p": 100, "cost": 600},
    {"id": 3, "name": "مدفع الذهب", "p": 250, "cost": 1500}
]

# --- [ واجهة اللعبة - HTML/CSS ] ---
async def handle_index(request):
    html = """
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON PRO</title>
        <style>
            body { background: #000; color: #FFD700; font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; }
            .card { border: 2px solid #FFD700; border-radius: 20px; padding: 20px; background: rgba(255, 215, 0, 0.05); box-shadow: 0 0 20px #FFD700; margin: 15px; }
            .bar { width: 100%; background: #222; height: 12px; border-radius: 10px; border: 1px solid #FFD700; margin: 5px 0; overflow: hidden; }
            .hp-fill { height: 100%; background: linear-gradient(90deg, #ff0000, #900); width: 100%; transition: 0.3s; }
            .xp-fill { height: 100%; background: linear-gradient(90deg, #00ff00, #008800); width: 0%; transition: 0.3s; }
            .btn { background: linear-gradient(45deg, #FFD700, #B8860B); border: none; padding: 15px; width: 100%; border-radius: 12px; font-weight: bold; margin: 8px 0; cursor: pointer; color: #000; font-size: 1.1em; }
            .monster { height: 150px; filter: drop-shadow(0 0 10px #FFD700); margin: 15px 0; }
            #shop { display: none; }
            .item { display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #333; }
        </style>
    </head>
    <body>
        <div id="game-scr" class="card">
            <h2 style="margin:0">⚔️ ARMAGEDDON ⚔️</h2>
            <div style="display:flex; justify-content:space-between; font-size:0.9em;">
                <span>🎖 المستوى: <span id="lvl">1</span></span>
                <span>🪙 الذهب: <span id="gold">100</span></span>
            </div>
            <div class="bar"><div id="hp-bar" class="hp-fill"></div></div>
            <div class="bar"><div id="xp-bar" class="xp-fill"></div></div>
            <img src="https://img.icons8.com/plasticine/200/dragon.png" class="monster">
            <div id="log" style="height:40px; font-size:0.8em; color:#fff;">الوحش ينتظر ضربتك!</div>
            <button class="btn" onclick="play('attack')">💥 هجوم كاسح</button>
            <button class="btn" style="background:#fff" onclick="toggleShop(true)">🏪 المتجر الملكي</button>
            <button class="btn" style="background:#444; color:#FFD700" onclick="play('gift')">🎁 هدية عشوائية</button>
        </div>

        <div id="shop" class="card">
            <h3>🏪 متجر الأسلحة</h3>
            <div id="items"></div>
            <button class="btn" style="background:gray; color:white" onclick="toggleShop(false)">🔙 عودة</button>
        </div>

        <script>
            function toggleShop(s) {
                document.getElementById('game-scr').style.display = s ? 'none' : 'block';
                document.getElementById('shop').style.display = s ? 'block' : 'none';
                if(s) loadItems();
            }
            async function play(t, id=null) {
                const r = await fetch(`/api/play?t=${t}&id=${id}`);
                const d = await r.json();
                document.getElementById('hp').innerText = d.hp;
                document.getElementById('gold').innerText = d.gold;
                document.getElementById('lvl').innerText = d.lvl;
                document.getElementById('hp-bar').style.width = d.hp + "%";
                document.getElementById('xp-bar').style.width = (d.exp % 100) + "%";
                document.getElementById('log').innerText = d.msg;
                if(d.success && t === 'buy') toggleShop(false);
            }
            function loadItems() {
                const list = [{id:1, n:"خنجر", c:200}, {id:2, n:"سيف", c:600}, {id:3, n:"مدفع", c:1500}];
                let html = '';
                list.forEach(i => { html += `<div class="item"><span>${i.n} (${i.c}🪙)</span><button onclick="play('buy', ${i.id})">شراء</button></div>`; });
                document.getElementById('items').innerHTML = html;
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

# --- [ API المعالجة ] ---
async def handle_api(request):
    t, i_id, uid = request.query.get('t'), request.query.get('id'), 12345
    db = db_conn.cursor()
    db.execute("SELECT * FROM players WHERE uid=?", (uid,))
    p = dict(db.fetchone() or {"gold":100, "hp":100, "exp":0, "lvl":1, "w_id":0})
    
    g, h, x, l, w = p['gold'], p['hp'], p['exp'], p['lvl'], p['w_id']
    msg, success = "", True

    if t == 'attack':
        pwr = next(it['p'] for it in WEAPONS if it['id'] == w)
        dmg, earn = random.randint(5, 15), random.randint(10, 30) + (pwr//5)
        h, g, x = max(0, h-dmg), g+earn, x+20
        if x >= l*100: l += 1; msg = f"🆙 ليفل جديد! أنت الآن مستوى {l}."
        else: msg = f"💥 ضربت بقوة {pwr}! كسبت {earn}🪙"
    elif t == 'gift':
        bonus = random.randint(20, 150)
        g += bonus; msg = f"🎁 مبروك! لقيت {bonus} ذهب في الطريق."
    elif t == 'buy':
        item = next((it for it in WEAPONS if str(it['id']) == i_id), None)
        if item and g >= item['cost']: g, w = g-item['cost'], item['id']; msg = f"⚔️ اشتريت {item['name']}!"
        else: msg, success = "❌ ذهبك لا يكفي!", False

    db.execute("INSERT OR REPLACE INTO players (uid, gold, hp, exp, lvl, w_id) VALUES (?,?,?,?,?,?)", (uid, g, h, x, l, w))
    db_conn.commit()
    return web.json_response({'gold':g, 'hp':h, 'exp':x, 'lvl':l, 'msg':msg, 'success':success})

# --- [ تشغيل البوت والويب ] ---
app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/api/play', handle_api)

@dp.message_handler(commands=['start'])
async def start(m: types.Message):
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔱 دخول اللعبة", web_app=types.WebAppInfo(url=WEB_URL)))
    await m.reply(f"أهلاً يا **محمد**! 🏆\nاللعبة دلوقت جاهزة وكاملة بنظام الليفلات.", reply_markup=kb)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    loop = asyncio.get_event_loop()
    loop.create_task(executor.start_polling(dp, skip_updates=True))
    web.run_app(app, host='0.0.0.0', port=port)
