import sqlite3, random, asyncio, os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web

# --- [ الإعدادات - استخدم التوكن الجديد ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- [ قاعدة البيانات المتطورة ] ---
def init_db():
    conn = sqlite3.connect('armageddon_v7.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()
    db.execute('''CREATE TABLE IF NOT EXISTS players 
                 (uid INTEGER PRIMARY KEY, gold INTEGER DEFAULT 100, hp INTEGER DEFAULT 100, 
                  weapon_id INTEGER DEFAULT 0, level INTEGER DEFAULT 1, last_claim TEXT)''')
    conn.commit()
    return conn

db_conn = init_db()

WEAPONS = [
    {"id": 0, "name": "قبضة اليد", "power": 10, "price": 0},
    {"id": 1, "name": "خنجر حديدي", "power": 35, "price": 150},
    {"id": 2, "name": "سيف الغضب", "power": 85, "price": 550},
    {"id": 3, "name": "الرمح الذهبي", "power": 200, "price": 1300}
]

# --- [ واجهة اللعبة - HTML5 الاحترافية ] ---
async def handle_index(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON</title>
        <style>
            body { background: #000; color: #FFD700; font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; overflow-x: hidden; }
            .card { border: 2px solid #FFD700; border-radius: 20px; padding: 20px; background: rgba(255, 215, 0, 0.05); box-shadow: 0 0 20px #FFD700; margin: 15px; position: relative; }
            .stats { display: flex; justify-content: space-between; font-weight: bold; font-size: 1.1em; margin-bottom: 10px; }
            .hp-bar { width: 100%; background: #222; height: 16px; border-radius: 10px; border: 1px solid #FFD700; overflow: hidden; margin: 10px 0; }
            .hp-fill { height: 100%; background: linear-gradient(90deg, #ff0000, #900); width: 100%; transition: 0.4s; }
            .btn { background: linear-gradient(45deg, #FFD700, #B8860B); border: none; padding: 15px; width: 100%; border-radius: 12px; font-weight: bold; margin: 6px 0; cursor: pointer; color: #000; font-size: 1.1em; box-shadow: 0 4px #664a00; }
            .btn:active { transform: translateY(2px); box-shadow: 0 2px #664a00; }
            .monster { height: 160px; filter: drop-shadow(0 0 12px #FFD700); margin: 20px 0; animation: bounce 2s infinite; }
            @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
            #shop { display: none; }
            .item-row { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; padding: 12px 5px; }
            #log { font-size: 0.9em; height: 40px; color: #fff; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div id="game-scr" class="card">
            <h2 style="margin:0">⚔️ ARMAGEDDON ⚔️</h2>
            <div class="stats">
                <span>🩸 <span id="hp">100</span>%</span>
                <span>🪙 <span id="gold">100</span></span>
            </div>
            <div class="hp-bar"><div id="hp-bar" class="hp-fill"></div></div>
            <img src="https://img.icons8.com/plasticine/200/monster-face.png" class="monster">
            <div id="log">الوحش يستعد للهجوم!</div>
            <button class="btn" onclick="play('attack')">💥 هجوم كاسح</button>
            <button class="btn" style="background:#fff; box-shadow: 0 4px #999;" onclick="toggleShop(true)">🏪 المتجر الملكي</button>
            <button class="btn" style="background:#444; color:#FFD700; box-shadow: 0 4px #222;" onclick="play('daily')">🎁 مكافأة يومية</button>
        </div>

        <div id="shop" class="card">
            <h3>🏪 متجر الأسلحة</h3>
            <div id="items-list"></div>
            <button class="btn" style="background:gray; color:white; box-shadow: 0 4px #333;" onclick="toggleShop(false)">🔙 عودة</button>
        </div>

        <script>
            function toggleShop(show) {
                document.getElementById('game-scr').style.display = show ? 'none' : 'block';
                document.getElementById('shop').style.display = show ? 'block' : 'none';
                if(show) loadItems();
            }

            async function play(type, id = null) {
                const res = await fetch(`/api/play?type=${type}&id=${id}`);
                const data = await res.json();
                document.getElementById('hp').innerText = data.hp;
                document.getElementById('gold').innerText = data.gold;
                document.getElementById('hp-bar').style.width = data.hp + "%";
                document.getElementById('log').innerText = data.msg;
                if(data.success && type === 'buy') toggleShop(false);
            }

            function loadItems() {
                const items = [
                    {id:1, name:"خنجر حديدي", p:150},
                    {id:2, name:"سيف الغضب", p:550},
                    {id:3, name:"الرمح الذهبي", p:1300}
                ];
                let h = '';
                items.forEach(i => {
                    h += `<div class="item-row"><span>${i.name} (${i.p}🪙)</span><button onclick="play('buy', ${i.id})" style="padding:5px 15px">شراء</button></div>`;
                });
                document.getElementById('items-list').innerHTML = h;
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

# --- [ API معالجة اللعب والمهمات ] ---
async def handle_api(request):
    q = request.query
    action, item_id, uid = q.get('type'), q.get('id'), 12345
    
    db = db_conn.cursor()
    db.execute("SELECT * FROM players WHERE uid = ?", (uid,))
    p = dict(db.fetchone() or {"gold": 100, "hp": 100, "weapon_id": 0})
    
    gold, hp, w_id = p['gold'], p['hp'], p['weapon_id']
    msg, success = "", True

    if action == 'attack':
        power = next(w['power'] for w in WEAPONS if w['id'] == w_id)
        dmg, earn = random.randint(5, 12), random.randint(10, 25) + (power // 4)
        hp, gold = max(0, hp - dmg), gold + earn
        msg = f"💥 ضربت بقوة {power}! كسبت {earn}🪙"
    
    elif action == 'daily':
        gold += 100
        msg = "🎁 استلمت 100🪙 مكافأة يومية!"
    
    elif action == 'buy':
        item = next((w for w in WEAPONS if str(w['id']) == item_id), None)
        if item and gold >= item['price']:
            gold, w_id = gold - item['price'], item['id']
            msg = f"⚔️ اشتريت {item['name']}!"
        else:
            msg, success = "❌ الذهب لا يكفي!", False

    db.execute("INSERT OR REPLACE INTO players (uid, gold, hp, weapon_id) VALUES (?, ?, ?, ?)", (uid, gold, hp, w_id))
    db_conn.commit()
    return web.json_response({'gold': gold, 'hp': hp, 'msg': msg, 'success': success})

# --- [ تشغيل البوت والسيرفر بذكاء ] ---
app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/api/play', handle_api)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🔱 دخول المعركة (Neon Gold)", web_app=types.WebAppInfo(url=WEB_URL))
    )
    await message.reply(f"🏆 مرحباً بك يا **محمد** في ARMAGEDDON\n\nاللعبة دلوقت كاملة وشغالة بنظام الـ WebApp الفاخر.", reply_markup=kb, parse_mode="Markdown")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    loop = asyncio.get_event_loop()
    loop.create_task(executor.start_polling(dp, skip_updates=True))
    web.run_app(app, host='0.0.0.0', port=port)
