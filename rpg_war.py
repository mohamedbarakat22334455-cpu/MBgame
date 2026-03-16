import sqlite3, random, asyncio, os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- [ الإعدادات ] ---
API_TOKEN = '8663020855:AAFr5eSCwu_cztS2e-bRvke6GixUhtolRyk'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- [ نظام الويب لـ Railway ] ---
async def handle(request):
    return web.Response(text="👑 ARMAGEDDON IS ONLINE & RUNNING!")

app = web.Application()
app.router.add_get('/', handle)

# --- [ قاعدة البيانات ] ---
conn = sqlite3.connect('armageddon_v2.db', check_same_thread=False)
db = conn.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS players 
             (uid INTEGER PRIMARY KEY, name TEXT, gold INTEGER DEFAULT 100, 
              hp INTEGER DEFAULT 100, max_hp INTEGER DEFAULT 100, 
              level INTEGER DEFAULT 1, xp INTEGER DEFAULT 0, 
              weapon TEXT DEFAULT 'قبضة اليد', attack INTEGER DEFAULT 10, 
              potions INTEGER DEFAULT 1, kills INTEGER DEFAULT 0)''')
conn.commit()

def get_player(uid, name="محارب"):
    db.execute("SELECT * FROM players WHERE uid = ?", (uid,))
    p = db.fetchone()
    if not p:
        db.execute("INSERT INTO players (uid, name) VALUES (?, ?)", (uid, name))
        conn.commit()
        return [uid, name, 100, 100, 100, 1, 0, 'قبضة اليد', 10, 1, 0]
    return list(p)

# --- [ القائمة الرئيسية ] ---
@dp.message_handler(commands=['start'])
async def main_menu(message: types.Message):
    p = get_player(message.from_user.id, message.from_user.full_name)
    kb = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("⚔️ دخول الساحة", callback_data="fight"),
        InlineKeyboardButton("🏪 المتجر", callback_data="shop"),
        InlineKeyboardButton("👤 ملفي", callback_data="profile"),
        InlineKeyboardButton("🏆 الأساطير", callback_data="top")
    )
    await message.reply(f"🛡 **مرحباً بك في ARMAGEDDON**\n\n🎖 ليفل: {p[5]} | 💀 قتلى: {p[10]}\n🩸 دم: {p[3]}/{p[4]}\n🪙 ذهب: {p[2]}\n⚔️ سلاحك: {p[7]}", reply_markup=kb)

# --- [ نظام المتجر والأسلحة ] ---
@dp.callback_query_handler(lambda c: c.data == "shop")
async def shop(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton("🧪 جرعة شفاء (30 ذهب)", callback_data="buy_pot"),
        InlineKeyboardButton("⚔️ سيف حديدي (150 ذهب)", callback_data="buy_sword"),
        InlineKeyboardButton("🛡 درع ملكي (300 ذهب)", callback_data="buy_armor"),
        InlineKeyboardButton("🔙 عودة", callback_data="back")
    )
    await call.message.edit_text("🏪 **المتجر الملكي**\nطوّر عتادك لتصمد في الساحة:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("buy_"))
async def buy_logic(call: types.CallbackQuery):
    uid = call.from_user.id
    p = get_player(uid)
    item = call.data.split("_")[1]
    
    if item == "pot" and p[2] >= 30:
        db.execute("UPDATE players SET gold = gold - 30, potions = potions + 1 WHERE uid = ?", (uid,))
        await call.answer("🧪 اشتريت جرعة شفاء!")
    elif item == "sword" and p[2] >= 150:
        db.execute("UPDATE players SET gold = gold - 150, weapon = 'سيف حديدي', attack = 25 WHERE uid = ?", (uid,))
        await call.answer("⚔️ مبروك! حصلت على السيف الحديدي.")
    else:
        await call.answer("❌ ذهبك لا يكفي!", show_alert=True)
    conn.commit()

# --- [ نظام القتال المطور ] ---
@dp.callback_query_handler(lambda c: c.data == "fight")
async def battle(call: types.CallbackQuery):
    p = get_player(call.from_user.id)
    if p[3] <= 20: return await call.answer("❌ صحتك منخفضة!", show_alert=True)
    
    m_hp = random.randint(40, 100) * p[5]
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🗡 هجوم", callback_data=f"hit_{m_hp}"),
        InlineKeyboardButton("🏃 هروب", callback_data="back")
    )
    await call.message.edit_text(f"👾 **ظهر لك وحش غاضب!**\n🩸 دمه: {m_hp}\n\nاستعد للقتال!", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("hit_"))
async def hit_logic(call: types.CallbackQuery):
    uid = call.from_user.id
    m_hp = int(call.data.split("_")[1])
    p = get_player(uid)
    
    p_hit = random.randint(p[8], p[8] + 10)
    m_hit = random.randint(5, 15)
    
    new_m_hp = max(0, m_hp - p_hit)
    new_p_hp = max(0, p[3] - m_hit)
    
    db.execute("UPDATE players SET hp = ? WHERE uid = ?", (new_p_hp, uid))
    conn.commit()

    if new_m_hp <= 0:
        db.execute("UPDATE players SET gold = gold + 50, kills = kills + 1 WHERE uid = ?", (uid,))
        conn.commit()
        return await call.message.edit_text("🏆 **هزمت الوحش وكسبت 50 ذهب!**", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 عودة", callback_data="back")))

    if new_p_hp <= 0:
        return await call.message.edit_text("💀 **سقطت في المعركة!**", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 عودة", callback_data="back")))

    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🗡 استمرار الهجوم", callback_data=f"hit_{new_m_hp}"))
    await call.message.edit_text(f"💥 ضربت الوحش بـ {p_hit}!\n🩸 دمك: {new_p_hp} | 🩸 دمه: {new_m_hp}", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "back")
async def back_to_menu(call: types.CallbackQuery):
    await call.message.delete()
    await main_menu(call.message)

# --- [ محرك التشغيل الاحترافي ] ---
async def on_startup(dp):
    await bot.delete_webhook()
    print("✅ ARMAGEDDON CONNECTED TO TELEGRAM")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    loop = asyncio.get_event_loop()
    loop.create_task(executor.start_polling(dp, skip_updates=True, on_startup=on_startup))
    web.run_app(app, host='0.0.0.0', port=port)
