import sqlite3, random, asyncio, os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- [ إعدادات MBAB ARMAGEDDON ] ---
# يا محمد تأكد إن ده توكن بوت ARMAGEDDON الجديد
API_TOKEN = '8533015825:AAGy7A-Abn3qqW8lwa7b93-Ii92wNTRP_cU'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- [ خادم الويب لإرضاء Railway ] ---
async def handle(request):
    return web.Response(text="👑 MBAB: ARMAGEDDON IS FULLY OPERATIONAL 🚀")

app = web.Application()
app.router.add_get('/', handle)

# --- [ نظام قاعدة البيانات المطور ] ---
def init_db():
    conn = sqlite3.connect('mbab_rpg.db', check_same_thread=False)
    db = conn.cursor()
    db.execute('''CREATE TABLE IF NOT EXISTS players 
                 (user_id INTEGER PRIMARY KEY, name TEXT, hp INTEGER DEFAULT 100, 
                  max_hp INTEGER DEFAULT 100, attack INTEGER DEFAULT 15, 
                  gold INTEGER DEFAULT 50, xp INTEGER DEFAULT 0, 
                  level INTEGER DEFAULT 1, potions INTEGER DEFAULT 1, kills INTEGER DEFAULT 0)''')
    conn.commit()
    return conn

conn = init_db()

def get_p(uid, name="محارب"):
    db = conn.cursor()
    db.execute("SELECT hp, max_hp, attack, gold, xp, level, potions, kills FROM players WHERE user_id = ?", (uid,))
    p = db.fetchone()
    if not p:
        db.execute("INSERT INTO players (user_id, name) VALUES (?, ?)", (uid, name))
        conn.commit()
        return [100, 100, 15, 50, 0, 1, 1, 0]
    return list(p)

# --- [ واجهة التحكم ] ---
@dp.message_handler(commands=['start'])
async def main_menu(message: types.Message):
    uid = message.from_user.id
    p = get_p(uid, message.from_user.full_name)
    
    kb = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("⚔️ ساحة القتال", callback_data="fight"),
        InlineKeyboardButton("🛒 المتجر الملكي", callback_data="shop"),
        InlineKeyboardButton("🏆 قائمة الأساطير", callback_data="top"),
        InlineKeyboardButton("👤 ملفي الشخصي", callback_data="profile")
    )
    
    await message.reply(
        f"🛡 **مرحباً بك في ARMAGEDDON** 🛡\n\n"
        f"🎖 المستوى: {p[5]} | 💀 القتلى: {p[7]}\n"
        f"🩸 الصحة: {p[0]}/{p[1]}\n"
        f"🪙 الذهب: {p[3]} | 🧪 الجرعات: {p[6]}\n\n"
        f"يا بطل، الأرض بانتظار شجاعتك!", 
        reply_markup=kb, parse_mode="Markdown"
    )

# --- [ نظام القتال المطور ] ---
@dp.callback_query_handler(lambda c: c.data == "fight")
async def start_fight(call: types.CallbackQuery):
    uid = call.from_user.id
    p = get_p(uid)
    if p[0] <= 10:
        return await call.answer("❌ صحتك ضعيفة جداً! اشترِ جرعة علاج أولاً.", show_alert=True)
    
    monsters = [("تنين الجليد 🧊", 60), ("سياف الظلام 🗡", 40), ("الغول العملاق 👹", 80)]
    m_name, m_hp_base = random.choice(monsters)
    m_hp = m_hp_base + (p[5] * 10)
    
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("⚔️ هجوم سريع", callback_data=f"hit_{m_hp}"),
        InlineKeyboardButton("🏃 انسحاب", callback_data="back")
    )
    await call.message.edit_text(f"👾 ظهر لك **{m_name}**!\n🩸 دمه: {m_hp}\n\nماذا ستفعل؟", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data.startswith("hit_"))
async def battle_engine(call: types.CallbackQuery):
    uid = call.from_user.id
    m_hp = int(call.data.split("_")[1])
    p = get_p(uid)
    
    p_dmg = random.randint(p[2], p[2] + 10)
    m_dmg = random.randint(5, 15 + p[5])
    
    new_m_hp = max(0, m_hp - p_dmg)
    new_p_hp = max(0, p[0] - m_dmg)
    
    # تحديث الصحة في القاعدة
    db = conn.cursor()
    db.execute("UPDATE players SET hp = ? WHERE user_id = ?", (new_p_hp, uid))
    conn.commit()

    if new_m_hp <= 0:
        gold_gain = 20 + (p[5] * 5)
        db.execute("UPDATE players SET gold = gold + ?, kills = kills + 1, xp = xp + 50 WHERE user_id = ?", (gold_gain, uid))
        conn.commit()
        return await call.message.edit_text(f"🎊 **انتصرت!**\n💰 كسبت {gold_gain} ذهب.\n💀 زاد عدد قتلاك.", 
                                         reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 عودة", callback_data="back")))

    if new_p_hp <= 0:
        return await call.message.edit_text("💀 **انتهت رحلتك هنا..**\nعد مجدداً بعد الاستشفاء.", 
                                         reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🏕 العودة للمعسكر", callback_data="back")))

    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🗡 استمرار الهجوم", callback_data=f"hit_{new_m_hp}"))
    await call.message.edit_text(f"💥 ضربته بـ {p_dmg}!\n🩸 دمك: {new_p_hp}\n🩸 دمه: {new_m_hp}", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "back")
async def back_to_start(call: types.CallbackQuery):
    await call.message.delete()
    await main_menu(call.message)

# --- [ محرك التشغيل الاحترافي ] ---
async def start_bot():
    print("🤖 ARMAGEDDON BOT IS ONLINE!")
    try:
        await dp.start_polling()
    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    loop = asyncio.get_event_loop()
    # تشغيل البوت في الخلفية مع الـ Web Server
    loop.create_task(start_bot())
    print(f"🚀 Deployment Successful on Port {port}")
    web.run_app(app, host='0.0.0.0', port=port)
