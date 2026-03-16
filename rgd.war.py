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
    conn = sqlite3.connect('armageddon_pro.db', check_same_thread=False)
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
    {"id": 1, "name": "خنجر حديدي", "power": 30, "price": 150},
    {"id": 2, "name": "سيف الغضب", "power": 70, "price": 500},
    {"id": 3, "name": "الرمح الذهبي", "power": 150, "price": 1200}
]

# --- [ واجهة اللعبة - HTML/CSS الفخمة ] ---
async def handle_index(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON WAR</title>
        <style>
            body { background: #000; color: #FFD700; font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; }
            .screen { display: none; padding: 15px; }
            .active { display: block; }
            .card { border: 2px solid #FFD700; border-radius: 15px; padding: 15px; background: rgba(255, 215, 0, 0.05); box-shadow: 0 0 15px #FFD700; }
            .btn { background: linear-gradient(45deg, #FFD700, #B8860B); border: none; padding: 12px; width: 100%; border-radius: 8px; font-weight: bold; margin: 5px 0; cursor: pointer; color: #000; }
            .hp-bar { width: 100%; background: #333; height: 15px; border-radius: 10px; margin: 10px 0; border: 1px solid #FFD700; overflow: hidden; }
            .hp-fill { height: 100%; background: red; transition: 0.3s; width: 100%; }
            .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; font-weight: bold; }
            .monster-img { height: 150px; filter: drop-shadow(0 0 10px #FFD700); margin: 10px 0; }
            .item { border-bottom: 1px solid #333; padding: 10px; display: flex; justify-content: space-between; align-items: center; }
        </style>
    </head>
    <body>
        <div id="fight-screen" class="screen active">
            <div class="card">
                <h2 style="margin:5px">🛡 ARMAGEDDON</h2>
                <div class="stats-grid">
                    <div>🩸 <span id="hp">100</span>%</div>
                    <div>🪙 <span id="gold">100</span></div>
                </div>
                <div class="hp-bar"><div id="hp-bar" class="hp-fill"></div></div>
                <img src="https://img.icons8.com/plasticine/200/monster-face.png" class="monster-img">
                <div id="log" style="height:35px; font-size:0.9em">استعد للمعركة!</div>
                <button class="btn" onclick="gameAction('attack')">⚔️ هجوم</button>
                <button class="btn" style="background:#fff" onclick="switchScreen('shop-screen')">🏪 المتجر</button>
            </div>
        </div>

        <div id="shop-screen" class="screen">
            <div class="card">
                <h3>🏪 المتجر الملكي</h3>
                <div id="shop-items"></div>
                <button class="btn" style="background:gray; color:white" onclick="switchScreen('fight-screen')">🔙 عودة</button>
            </div>
        </div>

        <script>
            function switchScreen(id) {
                document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
                document.getElementById(id).classList.add('active');
                if(id === 'shop-screen') loadShop();
            }

            async function gameAction(type, itemId = null) {
                const res = await fetch(`/api/play?type=${type}&item=${itemId}`);
                const data = await res.json();
                document.getElementById('hp').innerText = data.hp;
                document.getElementById('gold').innerText = data.gold;
                document.getElementById('hp-bar').style.width = data.hp + "%";
                document.getElementById('log').innerText = data.msg;
                if(data.success && type === 'buy') switchScreen('fight-screen');
            }

            function loadShop() {
                const items = [
                    {id: 1, name: "خنجر حديدي", price: 150},
                    {id: 2, name: "سيف الغضب", price: 500},
                    {id: 3, name: "الرمح الذهبي", price: 1200}
                ];
                let html = '';
                items.forEach(i => {
                    html += `<div class="item"><span>${i.name} (${i.price}🪙)</span><button onclick="gameAction('buy', ${i.id})" style="padding:5px">شراء</button></div>`;
                });
                document.getElementById('shop-items').innerHTML = html;
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

# --- [ API السيرفر ] ---
async def handle_play(request):
    action = request.query.get('type')
    item_id = request.query.get('item')
    uid = 12345 
    
    db = db_conn.cursor()
    db.execute("SELECT * FROM players WHERE uid = ?", (uid,))
    p = dict(db.fetchone() or {"gold": 100, "hp": 100, "weapon_id": 0, "level": 1})
    
    gold, hp, w_id = p['gold'], p['hp'], p['weapon_id']
    msg, success = "", True

    if action == 'attack':
        power = next(w['power'] for w in WEAPONS if w['id'] == w_id)
        dmg = random.randint(5, 12)
        earn = random.randint(10, 20) + (power // 5)
        hp = max(0, hp - dmg)
        gold += earn
        msg = f"💥 ضربت بقوة {power}! كسبت {earn}🪙"
    
    elif action == 'buy':
        item = next((w for w in WEAPONS if str(w['id']) == item_id), None)
        if item and gold >= item['price']:
            gold -= item['price']
            w_id = item['id']
            msg = f"⚔️ تم شراء {item['name']}!"
        else:
            msg = "❌ الذهب لا يكفي!"
            success = False

    db.execute("INSERT OR REPLACE INTO players (uid, gold, hp, weapon_id) VALUES (?, ?, ?, ?)", (uid, gold, hp, w_id))
    db_conn.commit()
    return web.json_response({'gold': gold, 'hp': hp, 'msg': msg, 'success': success})

app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/api/play', handle_play)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🎮 ابدأ اللعبة", web_app=types.WebAppInfo(url=WEB_URL))
    )
    await message.reply("🏆 مرحباً بك في **ARMAGEDDON**\nجاهز للمعركة يا بطل؟", reply_markup=kb, parse_mode="Markdown")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    loop = asyncio.get_event_loop()
    loop.create_task(executor.start_polling(dp, skip_updates=True))
    web.run_app(app, host='0.0.0.0', port=port)
