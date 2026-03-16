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
def init_db():
    conn = sqlite3.connect('armageddon_vFinal.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()
    db.execute('''CREATE TABLE IF NOT EXISTS players 
                 (uid INTEGER PRIMARY KEY, gold INTEGER DEFAULT 100, hp INTEGER DEFAULT 100, 
                  weapon_id INTEGER DEFAULT 0, level INTEGER DEFAULT 1)''')
    conn.commit()
    return conn

db_conn = init_db()

WEAPONS = [
    {"id": 0, "name": "قبضة اليد", "power": 10, "price": 0},
    {"id": 1, "name": "خنجر حديدي", "power": 35, "price": 150},
    {"id": 2, "name": "سيف الغضب", "power": 80, "price": 500},
    {"id": 3, "name": "الرمح الذهبي", "power": 180, "price": 1200}
]

# --- [ واجهة اللعبة - HTML/CSS ] ---
async def handle_index(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON</title>
        <style>
            body { background: #000; color: #FFD700; font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; padding: 10px; }
            .card { border: 2px solid #FFD700; border-radius: 20px; padding: 20px; background: rgba(255, 215, 0, 0.05); box-shadow: 0 0 20px #FFD700; }
            .btn { background: linear-gradient(45deg, #FFD700, #B8860B); border: none; padding: 15px; width: 100%; border-radius: 10px; font-weight: bold; margin: 5px 0; cursor: pointer; color: #000; font-size: 1.1em; }
            .hp-bar { width: 100%; background: #333; height: 15px; border-radius: 10px; margin: 10px 0; border: 1px solid #FFD700; overflow: hidden; }
            .hp-fill { height: 100%; background: linear-gradient(90deg, #ff0000, #b30000); width: 100%; transition: 0.3s; }
            .stats { display: flex; justify-content: space-around; font-weight: bold; margin: 10px 0; }
            .monster { height: 140px; filter: drop-shadow(0 0 10px #FFD700); margin: 15px 0; }
            .shop-item { border-bottom: 1px solid #333; padding: 10px; display: flex; justify-content: space-between; align-items: center; }
            #shop { display: none; }
        </style>
    </head>
    <body>
        <div id="game" class="card">
            <h1 style="margin:5px">🛡 ARMAGEDDON</h1>
            <div class="stats">
                <span>🩸 <span id="hp">100</span>%</span>
                <span>🪙 <span id="gold">100</span></span>
            </div>
            <div class="hp-bar"><div id="hp-bar" class="hp-fill"></div></div>
            <img src="https://img.icons8.com/plasticine/200/monster-face.png" class="monster">
            <div id="log" style="height:40px; font-size:0.85em; color: white;">اضغط هجوم لبدء المعركة!</div>
            <button class="btn" onclick="play('attack')">⚔️ هجوم كاسح</button>
            <button class="btn" style="background:#fff" onclick="toggleShop()">🏪 المتجر الملكي</button>
        </div>

        <div id="shop" class="card">
            <h3>🏪 متجر الأسلحة</h3>
            <div id="items-list"></div>
            <button class="btn" style="background:gray; color:white" onclick="toggleShop()">🔙 عودة للقتال</button>
        </div>

        <script>
            function toggleShop() {
                const g = document.getElementById('game');
                const s = document.getElementById('shop');
                if(g.style.display === 'none') { g.style.display='block'; s.style.display='none'; }
                else { g.style.display='none'; s.style.display='block'; loadShop(); }
            }

            async function play(type, id = null) {
                const res = await fetch(`/api/play?type=${type}&id=${id}`);
                const data = await res.json();
                document.getElementById('hp').innerText = data.hp;
                document.getElementById('gold').innerText = data.gold;
                document.getElementById('hp-bar').style.width = data.hp + "%";
                document.getElementById('log').innerText = data.msg;
                if(data.success && type === 'buy') toggleShop();
            }

            function loadShop() {
                const items = [
                    {id:1, name:"خنجر حديدي", price:150},
                    {id:2, name:"سيف الغضب", price:500},
                    {id:3, name:"الرمح الذهبي", price:1200}
                ];
                let h = '';
                items.forEach(i => {
                    h += `<div class="shop-item"><span>${i.name} (${i.price}🪙)</span><button onclick="play('buy', ${i.id})">شراء</button></div>`;
                });
                document.getElementById('items-list').innerHTML = h;
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

# --- [ API الخلفية ] ---
async def handle_api(request):
    action = request.query.get('type')
    item_id = request.query.get('id')
    uid = 12345 # سيتم ربطه بـ Telegram ID
    
    db = db_conn.cursor()
    db.execute("SELECT * FROM players WHERE uid = ?", (uid,))
    p = dict(db.fetchone() or {"gold": 100, "hp": 100, "weapon_id": 0})
    
    gold, hp, w_id = p['gold'], p['hp'], p['weapon_id']
    msg, success = "", True

    if action == 'attack':
        power = next(w['power'] for w in WEAPONS if w['id'] == w_id)
        dmg = random.randint(5, 12)
        earn = random.randint(10, 25) + (power // 5)
        hp = max(0, hp - dmg)
        gold += earn
        msg = f"💥 ضربت بقوة {power}! كسبت {earn} ذهب ونقص دمك {dmg}%"
    
    elif action == 'buy':
        item = next((w for w in WEAPONS if str(w['id']) == item_id), None)
        if item and gold >= item['price']:
            gold -= item['price']
            w_id = item['id']
            msg = f"⚔️ مبروك! اشتريت {item['name']}"
        else:
            msg = "❌ الذهب لا يكفي!"
            success = False

    db.execute("INSERT OR REPLACE INTO players (uid, gold, hp, weapon_id) VALUES (?, ?, ?, ?)", (uid, gold, hp, w_id))
    db_conn.commit()
    return web.json_response({'gold': gold, 'hp': hp, 'msg': msg, 'success': success})

app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/api/play', handle_api)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🎮 ابدأ اللعبة (شاشة كاملة)", web_app=types.WebAppInfo(url=WEB_URL))
    )
    await message.reply("🏆 أهلاً بك في **ARMAGEDDON**\nجاهز للمعركة؟", reply_markup=kb, parse_mode="Markdown")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    loop = asyncio.get_event_loop()
    loop.create_task(executor.start_polling(dp, skip_updates=True))
    web.run_app(app, host='0.0.0.0', port=port)
