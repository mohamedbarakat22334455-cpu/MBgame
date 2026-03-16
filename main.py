import os, sqlite3, random, asyncio
from aiogram import Bot, Dispatcher, types
from aiohttp import web

# --- [ الإعدادات - التوكن والروابط ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- [ قاعدة البيانات الشاملة ] ---
def init_db():
    conn = sqlite3.connect('armageddon_full.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()
    db.execute('''CREATE TABLE IF NOT EXISTS players 
                 (uid INTEGER PRIMARY KEY, gold INTEGER DEFAULT 100, hp INTEGER DEFAULT 100, 
                  lvl INTEGER DEFAULT 1, weapon_id INTEGER DEFAULT 0)''')
    conn.commit()
    return conn

db_conn = init_db()

WEAPONS = [
    {"id": 0, "name": "قبضة اليد", "power": 10, "price": 0},
    {"id": 1, "name": "الخنجر الحديدي", "power": 35, "price": 200},
    {"id": 2, "name": "سيف الغضب", "power": 90, "price": 700},
    {"id": 3, "name": "الرمح الذهبي", "power": 250, "price": 2000}
]

# --- [ واجهة اللعبة - تصميم النيون جولد الاحترافي ] ---
async def handle_game(request):
    html = """
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON</title>
        <style>
            :root { --gold: #FFD700; --neon: #ffaa00; }
            body { background: #000; color: var(--gold); font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; padding: 15px; }
            .card { border: 2px solid var(--gold); border-radius: 20px; padding: 20px; background: rgba(255, 215, 0, 0.05); box-shadow: 0 0 25px rgba(255, 215, 0, 0.2); }
            .stats { display: flex; justify-content: space-around; font-weight: bold; font-size: 1.1em; margin-bottom: 15px; }
            .bar { width: 100%; background: #222; height: 14px; border-radius: 10px; border: 1px solid var(--gold); margin: 8px 0; overflow: hidden; }
            .hp-fill { background: linear-gradient(90deg, #ff0000, #900); height: 100%; width: 100%; transition: 0.4s; }
            .btn { background: linear-gradient(45deg, var(--gold), #B8860B); border: none; padding: 15px; width: 100%; border-radius: 12px; font-weight: bold; margin: 8px 0; cursor: pointer; color: #000; font-size: 1.1em; box-shadow: 0 4px #664a00; }
            .btn:active { transform: translateY(2px); }
            .monster { height: 160px; filter: drop-shadow(0 0 15px var(--gold)); margin: 15px 0; animation: pulse 2s infinite; }
            @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
            #log { color: #fff; font-size: 0.9em; height: 45px; margin-top: 10px; }
            #shop { display: none; }
            .shop-item { display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #333; align-items: center; }
        </style>
    </head>
    <body>
        <div id="game-scr" class="card">
            <h2 style="margin: 0;">🛡 ARMAGEDDON</h2>
            <div class="stats">
                <span>🩸 <span id="hp">100</span>%</span>
                <span>🪙 <span id="gold">100</span></span>
                <span>🎖 ليفل <span id="lvl">1</span></span>
            </div>
            <div class="bar"><div id="hp-bar" class="hp-fill"></div></div>
            <img src="https://img.icons8.com/plasticine/200/fire-dragon.png" class="monster">
            <div id="log">الوحش الأسطوري في انتظارك!</div>
            <button class="btn" onclick="play('attack')">⚔️ هجوم مدمر</button>
            <button class="btn" style="background: #fff;" onclick="toggleShop(true)">🏪 المتجر الملكي</button>
            <button class="btn" style="background: #444; color: var(--gold);" onclick="play('daily')">🎁 مكافأة يومية</button>
        </div>

        <div id="shop" class="card">
            <h3>🏪 متجر الأسلحة الملكي</h3>
            <div id="items-list"></div>
            <button class="btn" style="background: gray; color: white;" onclick="toggleShop(false)">🔙 عودة للمعركة</button>
        </div>

        <script>
            function toggleShop(s) {
                document.getElementById('game-scr').style.display = s ? 'none' : 'block';
                document.getElementById('shop').style.display = s ? 'block' : 'none';
                if(s) loadShop();
            }
            async function play(type, id = null) {
                const res = await fetch(`/api/play?type=${type}&id=${id}`);
                const d = await res.json();
                document.getElementById('gold').innerText = d.gold;
                document.getElementById('hp').innerText = d.hp;
                document.getElementById('lvl').innerText = d.lvl;
                document.getElementById('hp-bar').style.width = d.hp + "%";
                document.getElementById('log').innerText = d.msg;
                if(d.success && type === 'buy') toggleShop(false);
            }
            function loadShop() {
                const list = [{id:1, n:"خنجر", p:200}, {id:2, n:"سيف", p:700}, {id:3, n:"رمح ذهبي", p:2000}];
                let h = '';
                list.forEach(i => { h += `<div class="shop-item"><span>${i.n} (${i.p}🪙)</span><button onclick="play('buy', ${i.id})">شراء</button></div>`; });
                document.getElementById('items-list').innerHTML = h;
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

# --- [ API الخلفية - المنطق البرمجي ] ---
async def handle_api(request):
    type, item_id, uid = request.query.get('type'), request.query.get('id'), 12345
    db = db_conn.cursor()
    db.execute("SELECT * FROM players WHERE uid = ?", (uid,))
    p = dict(db.fetchone() or {"gold": 100, "hp": 100, "lvl": 1, "weapon_id": 0})
    
    g, h, l, w_id = p['gold'], p['hp'], p['lvl'], p['weapon_id']
    msg, success = "", True

    if type == 'attack':
        power = next(w['power'] for w in WEAPONS if w['id'] == w_id)
        dmg, earn = random.randint(5, 15), random.randint(10, 30) + (power // 5)
        h, g = max(0, h - dmg), g + earn
        if random.random() < 0.1: l += 1; msg = f"🆙 مبروك! ليفل جديد {l}."
        else: msg = f"💥 هجوم بـ {power} قوة! كسبت {earn} ذهب."
    elif type == 'daily':
        g += 150; msg = "🎁 استلمت 150 ذهب مكافأة يومية!"
    elif type == 'buy':
        item = next((w for w in WEAPONS if str(w['id']) == item_id), None)
        if item and g >= item['price']:
            g, w_id = g - item['price'], item['id']
            msg = f"⚔️ اشتريت {item['name']} بنجاح!"
        else:
            msg, success = "❌ الذهب لا يكفي!", False

    db.execute("INSERT OR REPLACE INTO players (uid, gold, hp, lvl, weapon_id) VALUES (?, ?, ?, ?, ?)", (uid, g, h, l, w_id))
    db_conn.commit()
    return web.json_response({'gold': g, 'hp': h, 'lvl': l, 'msg': msg, 'success': success})

# --- [ أوامر تليجرام - الرد الفوري ] ---
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🔱 دخول أرمجدون", web_app=types.WebAppInfo(url=WEB_URL))
    )
    await message.reply(f"🏆 أهلاً بك يا بطل في **ARMAGEDDON**\n\nأنا شغال دلوقت يا محمد والبوت جاهز للرد. ادخل الساحة الذهبية من الزرار تحت!", reply_markup=kb, parse_mode="Markdown")

# --- [ تشغيل السيرفر - الربط السحري ] ---
if __name__ == '__main__':
    app = web.Application()
    app.router.add_get('/', handle_game)
    app.router.add_get('/api/play', handle_api)
    
    port = int(os.environ.get("PORT", 8080))
    loop = asyncio.get_event_loop()
    
    # السر هنا: البوت بيشتغل كـ Task مستقل عشان ميعطلش السيرفر
    loop.create_task(dp.start_polling())
    web.run_app(app, host='0.0.0.0', port=port)
