import sqlite3, random, asyncio, datetime
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- [ إعدادات MBAB الرئيسية ] ---
API_TOKEN = 'YOUR_BOT_TOKEN' # ضع توكن البوت هنا
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- [ نظام قاعدة البيانات الشامل ] ---
conn = sqlite3.connect('mbab_rpg_master.db', check_same_thread=False)
db = conn.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS players 
             (user_id INTEGER PRIMARY KEY, name TEXT, hp INTEGER DEFAULT 100, 
              max_hp INTEGER DEFAULT 100, attack INTEGER DEFAULT 15, 
              gold INTEGER DEFAULT 50, xp INTEGER DEFAULT 0, 
              level INTEGER DEFAULT 1, potions INTEGER DEFAULT 1, 
              kills INTEGER DEFAULT 0, last_daily TEXT)''')
conn.commit()

# دالة جلب البيانات (تلقائية بالكامل)
def get_p(uid, name="محارب"):
    db.execute("SELECT hp, max_hp, attack, gold, xp, level, potions, kills, last_daily FROM players WHERE user_id = ?", (uid,))
    p = db.fetchone()
    if not p:
        db.execute("INSERT INTO players (user_id, name) VALUES (?, ?)", (uid, name))
        conn.commit()
        return (100, 100, 15, 50, 0, 1, 1, 0, "")
    return p

# --- [ الواجهة الرئيسية ] ---
@dp.message_handler(commands=['start'])
async def main_menu(message: types.Message):
    uid = message.from_user.id
    hp, m_hp, atk, gold, xp, lvl, pots, kills, _ = get_p(uid, message.from_user.full_name)
    
    kb = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("⚔️ دخول الساحة", callback_data="fight"),
        InlineKeyboardButton("🏪 المتجر", callback_data="shop"),
        InlineKeyboardButton("🎁 هدية يومية", callback_data="daily"),
        InlineKeyboardButton("🏆 الأساطير", callback_data="top"),
        InlineKeyboardButton("👤 ملفي", callback_data="profile")
    )
    
    await message.reply(f"⚔️ **مرحباً بك في أسطورة MBAB الحربية**\n\n"
                       f"🎖 المستوى: {lvl} | 💀 القتلى: {kills}\n"
                       f"🩸 الصحة: {hp}/{m_hp}\n"
                       f"🪙 الذهب: {gold} | 🧪 جرعات: {pots}\n\n"
                       f"جاهز للمعركة القادمة؟", reply_markup=kb)

# --- [ نظام القتال الملحمي ] ---
@dp.callback_query_handler(lambda c: c.data == "fight")
async def hunt(call: types.CallbackQuery):
    uid = call.from_user.id
    hp, _, _, _, _, lvl, _, _, _ = get_p(uid)
    
    if hp <= 0: return await call.answer("❌ طاقتك منتهية! اذهب للمتجر للعلاج.", show_alert=True)
    
    m_list = [("غول جبلي 👹", 50), ("هيكل عظمي 💀", 30), ("تنين ناري 🐲", 120)]
    m_name, m_hp_base = random.choice(m_list)
    m_hp = m_hp_base * lvl
    m_atk = 8 * lvl
    
    kb = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("⚔️ ضربة سيف", callback_data=f"hit_{m_hp}_{m_atk}"),
        InlineKeyboardButton(f"🧪 جرعة", callback_data=f"use_{m_hp}_{m_atk}"),
        InlineKeyboardButton("🏃 هروب", callback_data="back")
    )
    await call.message.edit_text(f"🚧 **ظهر لك {m_name}!**\n🩸 دمه: {m_hp}\n⚔️ قوته: {m_atk}", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith(("hit_", "use_")))
async def battle_logic(call: types.CallbackQuery):
    uid = call.from_user.id
    data = call.data.split("_")
    m_hp, m_atk = int(data[1]), int(data[2])
    hp, m_hp_p, atk, gold, xp, lvl, pots, kills, _ = get_p(uid)
    
    if data[0] == "use":
        if pots < 1: return await call.answer("❌ لا تملك جرعات!")
        db.execute("UPDATE players SET hp = ?, potions = potions - 1 WHERE user_id = ?", (min(m_hp_p, hp+50), uid))
        conn.commit()
        return await hunt(call)

    # حساب الضربات
    p_dmg = random.randint(atk, atk + 10)
    m_dmg = random.randint(m_atk - 5, m_atk + 5)
    
    new_m_hp = m_hp - p_dmg
    new_p_hp = max(0, hp - m_dmg)
    
    db.execute("UPDATE players SET hp = ? WHERE user_id = ?", (new_p_hp, uid))
    conn.commit()

    if new_p_hp <= 0:
        return await call.message.edit_text("💀 **سقطت في المعركة!** تم سلب بعض ذهبك.", 
                                         reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⛺️ العودة", callback_data="back")))

    if new_m_hp <= 0:
        reward = 25 * lvl
        xp_gain = 40 * lvl
        new_xp = xp + xp_gain
        msg = f"🏆 **نصر مؤزر!**\n💰 +{reward} ذهب | ✨ +{xp_gain} خبرة"
        
        if new_xp >= lvl * 150:
            db.execute("UPDATE players SET level = level + 1, xp = 0, attack = attack + 7, max_hp = max_hp + 25 WHERE user_id = ?", (uid,))
            msg += "\n🌟 **ارتقيت لمستوى جديد!**"
        else:
            db.execute("UPDATE players SET xp = ?, gold = gold + ?, kills = kills + 1 WHERE user_id = ?", (new_xp, reward, uid))
        conn.commit()
        return await call.message.edit_text(msg, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⚔️ وحش آخر", callback_data="fight")))

    kb = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("⚔️ اضرب!", callback_data=f"hit_{new_m_hp}_{m_atk}"),
        InlineKeyboardButton(f"🧪 ({pots})", callback_data=f"use_{new_m_hp}_{m_atk}")
    )
    await call.message.edit_text(f"💥 ضربته بـ {p_dmg}!\n🩸 دمك: {new_p_hp} | 🩸 دمه: {new_m_hp}", reply_markup=kb)

# --- [ الهدايا اليومية ] ---
@dp.callback_query_handler(lambda c: c.data == "daily")
async def daily_gift(call: types.CallbackQuery):
    uid = call.from_user.id
    today = str(datetime.date.today())
    _, _, _, _, _, _, _, _, last_day = get_p(uid)
    
    if last_day == today:
        return await call.answer("❌ استلمت هدية اليوم بالفعل! تعال غداً.", show_alert=True)
    
    gift = random.randint(50, 150)
    db.execute("UPDATE players SET gold = gold + ?, last_daily = ? WHERE user_id = ?", (gift, today, uid))
    conn.commit()
    await call.answer(f"🎁 مبروك! حصلت على {gift} ذهب هدية يومية.", show_alert=True)
    await back_to_menu(call)

# --- [ المتجر ولوحة الأساطير ] ---
@dp.callback_query_handler(lambda c: c.data == "shop")
async def shop(call: types.CallbackQuery):
    await call.message.edit_text("🛒 **متجر MBAB**\n\n1. علاج كامل (20 🪙) -> /buy_heal\n2. جرعة (40 🪙) -> /buy_pot\n3. سيف فولاذي (250 🪙) -> /buy_sword", 
                               reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 عودة", callback_data="back")))

@dp.callback_query_handler(lambda c: c.data == "top")
async def leaderboard(call: types.CallbackQuery):
    db.execute("SELECT name, level FROM players ORDER BY level DESC LIMIT 5")
    rows = db.fetchall()
    text = "🏆 **أساطير الحرب:**\n\n" + "\n".join([f"{i+1}. {r[0]} - ليفل {r[1]}" for i, r in enumerate(rows)])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 عودة", callback_data="back")))

@dp.callback_query_handler(lambda c: c.data == "back")
async def back_to_menu(call: types.CallbackQuery):
    await call.message.delete()
    await main_menu(call)

if __name__ == '__main__':
    print("🚀 MBAB WAR SUPREME IS READY!")
    executor.start_polling(dp, skip_updates=True)
