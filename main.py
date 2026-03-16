import os, sqlite3, random, asyncio, logging
from aiogram import Bot, Dispatcher, types
from aiohttp import web

# إعداد اللوجز لمراقبة السيرفر
logging.basicConfig(level=logging.INFO)

# --- [ الإعدادات - حط توكنك هنا ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- [ قاعدة البيانات - نظام الحفظ الذكي ] ---
conn = sqlite3.connect('armageddon_pro.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
db = conn.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS players 
             (uid INTEGER PRIMARY KEY, gold INTEGER DEFAULT 100, hp INTEGER DEFAULT 100, 
              lvl INTEGER DEFAULT 1, exp INTEGER DEFAULT 0, weapon_id INTEGER DEFAULT 0)''')
conn.commit()

# داتا الأسلحة والوحوش
WEAPONS = [
    {"name": "قبضة اليد", "power": 10, "price": 0},
    {"name": "خنجر النيون", "power": 45, "price": 300},
    {"name": "سيف الغضب", "power": 120, "price": 1000},
    {"name": "الرمح الأسطوري", "power": 400, "price": 3500}
]

MONSTERS = [
    {"name": "تنين النار", "img": "https://img.icons8.com/plasticine/200/fire-dragon.png"},
    {"name": "الغول العملاق", "img": "https://img.icons8.com/plasticine/200/ogre.png"},
    {"name": "الفارس المظلم", "img": "https://img.icons8.com/plasticine/200/knight.png"}
]

# --- [ واجهة اللعبة - تصميم Glassmorphism ذهبي كامل ] ---
async def handle_index(request):
    html = """
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON PRO</title>
        <style>
            body { background: radial-gradient(circle, #1a1a1a 0%, #000 100%); color: #FFD700; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 15px; display: flex; justify-content: center; }
            .glass-card { 
                background: rgba(255, 215, 0, 0.04); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
                border: 2px solid rgba(255, 215, 0, 0.3); border-radius: 30px; padding: 25px;
                width: 100%; max-width: 420px; text-align: center; box-shadow: 0 0 30px rgba(255, 215, 0, 0.15);
            }
            .stats-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 20px; font-weight: bold; font-size: 0.9em; }
            .bar-container { width: 100%; background: rgba(255,255,255,0.1); height: 14px; border-radius: 10px; border: 1px solid #FFD700; overflow: hidden; margin: 10px 0; }
            .hp-fill { background: linear-gradient(90deg, #ff0000, #900); height: 100%; width: 100%; transition: 0.4s; }
            .btn { 
                background: linear-gradient(45deg, #FFD700, #B8860B); border: none; padding: 16px; 
                width: 100%; border-radius: 15px; font-weight: bold; cursor: pointer; color: #000; margin: 8px 0;
                box-shadow: 0 4px 15px rgba(218, 165, 32, 0.4); font-size: 1em;
            }
            .btn:active { transform: scale(0.98); }
            .monster-img { height: 180px; filter: drop-shadow(0 0 20px #FFD700); margin: 15px 0; transition: 0.3s; }
            #log { color: #fff; font-size: 0.9em; min-height: 45px; margin-top: 10px; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 10px; }
            .shop-ui { display: none; }
        </style>
    </head>
    <body>
        <div class="glass-card" id="game-ui">
            <h1 style="margin:0 0 15px 0; text-shadow: 0 0 10px #FFD700;">🔱 ARMAGEDDON</h1>
            <div class="stats-grid">
                <div>🩸 <span id="hp">100</span>%</div>
                <div>🪙 <span id="gold">100</span></div>
                <div>🎖 ليفل <span id="lvl">1</span></div>
            </div>
            <div class="bar-container"><div id="hp-bar" class="hp-fill"></div></div>
            <img id="m-img" src="https://img.icons8.com/plasticine/200/fire-dragon.png" class="monster-img">
            <div id="log">الوحش الأسطوري يتحداك!</div>
            
            <button class="btn" onclick="play('attack')">⚔️ هجوم مدمر</button>
            <button class="btn" style="background:#fff" onclick="toggleShop(true)">🏪 المتجر الملكي</button>
            <button class="btn" style="background:#333; color:#FFD700" onclick="play('daily')">🎁 مكافأة يومية</button>
        </div>

        <div class="glass-card shop-ui" id="shop-ui">
            <h2>🏪 متجر الأسلحة</h2>
            <div id="items">
                <button class="btn" onclick="play('buy', 1)">شراء خنجر النيون (300🪙)</button>
                <button class="btn" onclick="play('buy', 2)">شراء سيف الغضب (1000🪙)</button>
                <button class="btn" onclick="play('buy', 3)">شراء الرمح الأسطوري (3500🪙)</button>
            </div>
            <button class="btn" style="background:#555; color:#fff" onclick="toggleShop(false)">🔙 عودة للمعركة</button>
        </div>

        <script>
            function toggleShop(s) {
                document.getElementById('game-ui').style.display = s ? 'none' : 'block';
                document.getElementById('shop-ui').style.display = s ? 'block' : 'none';
            }
            async function play(type, id=0) {
                const res = await fetch(`/api/play?type=${type}&id=${id}`);
                const d = await res.json();
                document.getElementById('gold').innerText = d.gold;
                document.getElementById('hp').innerText = d.hp;
                document.getElementById('lvl').innerText = d.lvl;
                document.getElementById('hp-bar').style.width = d.hp + "%";
                document.getElementById('log').innerText = d.msg;
                document.getElementById('m-img').src = d.m_img;
                if(type === 'buy' && d.success) toggleShop(false);
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

# --- [ API الخلفية - نظام اللعبة الاحترافي ] ---
async def handle_api(request):
    t, item_id = request.query.get('type'), request.query.get('id')
    user_id = 1 # للتبسيط في التجربة
    db_c = conn.cursor()
    db_c.execute("SELECT * FROM players WHERE uid = ?", (user_id,))
    p = dict(db_c.fetchone() or {"gold": 100, "hp": 100, "lvl": 1, "exp": 0, "weapon_id": 0})
    
    g, h, l, x, w_id = p['gold'], p['hp'], p['lvl'], p['exp'], p['weapon_id']
    msg, success = "", True
    monster = random.choice(MONSTERS)

    if t == 'attack':
        pwr = WEAPONS[w_id]['power']
        earn = random.randint(15, 35) + (pwr // 3)
        g += earn; h = max(0, h - 7); x += 25
        if x >= l * 100: l += 1; x = 0; msg = f"🆙 مبروك! ارتقيت للمستوى {l}!"
        else: msg = f"💥 ضربة بـ {WEAPONS[w_id]['name']}! كسبت {earn} ذهب."
    elif t == 'daily':
        g += 150; msg = "🎁 مكافأة ملكية: 150 ذهب!"
    elif t == 'buy':
        idx = int(item_id)
        if g >= WEAPONS[idx]['price']:
            g -= WEAPONS[idx]['price']; w_id = idx
            msg = f"⚔️ تم تجهيز {WEAPONS[idx]['name']}!"
        else: msg = "❌ ذهبك لا يكفي!"; success = False

    db_c.execute("INSERT OR REPLACE INTO players (uid, gold, hp, lvl, exp, weapon_id) VALUES (?, ?, ?, ?, ?, ?)", (user_id, g, h, l, x, w_id))
    conn.commit()
    return web.json_response({'gold': g, 'hp': h, 'lvl': l, 'msg': msg, 'm_img': monster['img'], 'success': success})

# --- [ أوامر البوت - الرد الفوري ] ---
@dp.message_handler(commands=['start'])
async def start(m: types.Message):
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔱 دخول أرمجدون", web_app=types.WebAppInfo(url=WEB_URL)))
    await m.reply(f"🏆 أهلاً بك يا بطل في **ARMAGEDDON**\n\nالبوت واللعبة شغالين دلوقتي. ادخل الساحة وابدأ تجميع الذهب!", reply_markup=kb)

# --- [ تشغيل السيرفر ] ---
if __name__ == '__main__':
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/play', handle_api)
    
    port = int(os.environ.get("PORT", 8080))
    loop = asyncio.get_event_loop()
    # السر هنا: تشغيل البوت في الخلفية بشكل يضمن عدم توقف السيرفر
    loop.create_task(dp.start_polling())
    web.run_app(app, host='0.0.0.0', port=port)
