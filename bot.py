import os
import asyncio
import logging
import random
import time
import json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import BotCommand, BotCommandScopeDefault, InlineKeyboardMarkup, InlineKeyboardButton
from supabase import create_client

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# =====================================================================
# ⚙️ КОНФИГ ЧЕРЕЗ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ (ENV)
# =====================================================================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# =====================================================================

# Инициализация бота и клиента Supabase
bot = Bot(token=TOKEN)
dp = Dispatcher()
db = create_client(URL, KEY)

# Premium Emoji IDs
PICKAXE_ID = "5197371802136892976"    
MONEY_BAG_ID = "5206223871467878339"  
BALANCE_ID = "5924587830675249107"    
ERROR_EMOJI_ID = "5240241223632954241" 

# Данные игры
CRYSTALS_DATA = {
    "Common": {"name": "Обычный кристалл", "id": "6269242583763913842", "price": 1000},
    "Rare": {"name": "Редкий кристалл", "id": "6269061400568532047", "price": 2500},
    "SuperRare": {"name": "Сверхредкий кристалл", "id": "6269383548885535501", "price": 5000},
    "Premium1": {"name": "Премиум кристалл 1", "id": "6269338864047578738", "price": 10000},
    "Premium2": {"name": "Премиум кристалл 2", "id": "6269384047578738", "price": 15000},
    "Premium3": {"name": "Premium Crystal 3", "id": "62693886404578738", "price": 20000}
}

CASES_DATA = {
    "wood": {"name": "📦 Деревянный кейс", "price": 5000, "min": 1000, "max": 12000},
    "iron": {"name": "🎁 Железный кейс", "price": 25000, "min": 5000, "max": 60000},
    "gold": {"name": "💎 Золотой кейс", "price": 100000, "min": 25000, "max": 250000},
    "diamond": {"name": "💠 Алмазный кейс", "price": 500000, "min": 150000, "max": 1200000}
}

SHOP_PICKS = {
    1: {"name": "Деревянная кирка", "price": 0, "mult": 1.0},
    2: {"name": "Каменная кирка", "price": 5000, "mult": 1.5},
    3: {"name": "Железная кирка", "price": 15000, "mult": 2.5},
    4: {"name": "Золотая кирка", "price": 50000, "mult": 5.0},
    5: {"name": "Алмазная кирка", "price": 150000, "mult": 10.0},
    6: {"name": "Изумрудная кирка", "price": 350000, "mult": 18.0},
    7: {"name": "🔱 Божественная кирка", "price": 15000000000, "mult": 200000.0}
}

active_miners = set()

# --- КЛАВИАТУРЫ ---
def get_main_keyboard():
    kb = [
        [types.KeyboardButton(text="⛏ Шахта"), types.KeyboardButton(text="🛒 Магазин")],
        [types.KeyboardButton(text="💳 Баланс"), types.KeyboardButton(text="🎒 Инвентарь")],
        [types.KeyboardButton(text="🎰 Кейсы"), types.KeyboardButton(text="💎 Продать камни")],
        [types.KeyboardButton(text="🏆 Топ игроков"), types.KeyboardButton(text="🎁 Бонус")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- РАБОТА С СУПАРБЕЙЗ (SUPABASE) ---
def get_player(user_id, username=None):
    res = db.table("players").select("*").eq("user_id", user_id).execute()
    
    if not res.data:
        # Вот здесь строка была разорвана, теперь всё зафиксировано в одну линию
        new_player = {
            "user_id": user_id, "balance": 0, "pick_lvl": 1, "used_promos": "", 
            "username": username, "last_bonus": 0, "inventory": "1", "crystals": "{}", "has_drill": 0
        }
        db.table("players").insert(new_player).execute()
        return {"balance": 0, "pick_lvl": 1, "used_promos": [], "last_bonus": 0, "inventory": [1], "crystals": {}, "username": username, "has_drill": 0}
    
    data = res.data[0]
    
    crystals_raw = data.get("crystals", "{}")
    if isinstance(crystals_raw, str):
        try:
            crystals_data = json.loads(crystals_raw) if crystals_raw else {}
        except json.JSONDecodeError:
            crystals_data = {}
    else:
        crystals_data = crystals_raw if crystals_raw else {}

    return {
        "balance": data["balance"], "pick_lvl": data["pick_lvl"], 
        "used_promos": data["used_promos"].split(",") if data["used_promos"] else [], 
        "last_bonus": data["last_bonus"], 
        "inventory": [int(x) for x in data["inventory"].split(",")] if data["inventory"] else [1],
        "crystals": crystals_data, 
        "username": data["username"], "has_drill": data["has_drill"]
    }

# --- ФОНОВЫЙ ДОХОД (БУР) ---
async def drill_income_task():
    while True:
        await asyncio.sleep(60)
        try:
            res = db.table("players").select("user_id, balance").eq("has_drill", 1).execute()
            for player in res.data:
                db.table("players").update({"balance": player["balance"] + 50}).eq("user_id", player["user_id"]).execute()
        except Exception as e:
            logging.error(f"Ошибка бура: {e}")

# --- ИГРОВОЙ ПРОЦЕСС ---
@dp.message(Command("start"))
async def main_start(message: types.Message):
    get_player(message.from_user.id, message.from_user.username)
    start_text = (
        f"<b>─── 〈 <tg-emoji emoji-id='{PICKAXE_ID}'>⛏</tg-emoji> MINER WORLD 〉 ───</b>\n\n"
        f"👋 Привет, <b>{message.from_user.full_name}</b>!\n"
        f"Добро пожаловать в симулятор шахтера.\n\n"
        f"Используй меню внизу экрана для управления своей карьерой!"
    )
    await message.answer(start_text, reply_markup=get_main_keyboard(), parse_mode="HTML")

@dp.message(F.text.in_({"⛏ Шахта", "/mine"}))
async def main_mine(message: types.Message):
    user_id = message.from_user.id
    if user_id in active_miners:
        return await message.reply(f'<tg-emoji emoji-id="{ERROR_EMOJI_ID}">🚫</tg-emoji> <b>Вы уже копаете!</b>', parse_mode="HTML")
    
    active_miners.add(user_id)
    p = get_player(user_id, message.from_user.username)
    
    status_msg = await message.answer(f'<tg-emoji emoji-id="{PICKAXE_ID}">⛏</tg-emoji> <b>Вы спустились в шахту...</b>\n\n⏳ Начинаем добычу ресурсов, ждите.', parse_mode="HTML")
    await asyncio.sleep(random.randint(4, 7))
    
    base_reward = random.randint(200, 600)
    is_crit = random.random() < 0.12
    crit_mult = 2 if is_crit else 1
    reward = int(base_reward * SHOP_PICKS[p["pick_lvl"]]["mult"] * crit_mult)
    
    crystal_msg = ""
    if random.random() < 0.35:
        rand_val = random.random()
        c_key = "Common" if rand_val > 0.5 else ("Rare" if rand_val > 0.2 else "SuperRare")
        crystal = CRYSTALS_DATA[c_key]
        p["crystals"][c_key] = p["crystals"].get(c_key, 0) + 1
        crystal_msg = f'\n✨ Находка: <tg-emoji emoji-id="{crystal["id"]}">💎</tg-emoji> <b>{crystal["name"]}</b>!'

    db.table("players").update({
        "balance": p["balance"] + reward, 
        "crystals": json.dumps(p["crystals"])
    }).eq("user_id", user_id).execute()
    
    active_miners.remove(user_id)
    crit_text = "<b>⚡ КРИТИЧЕСКИЙ УДАР (X2)!</b>\n" if is_crit else ""
    try: 
        await status_msg.delete()
    except Exception: 
        pass
    await message.answer(f'<tg-emoji emoji-id="{MONEY_BAG_ID}">💰</tg-emoji> <b>Успешно!</b>\n{crit_text}+ {reward} монет{crystal_msg}', parse_mode="HTML")

@dp.message(F.text.in_({"🎰 Кейсы", "/cases"}))
async def cases_menu(message: types.Message):
    kb = [[InlineKeyboardButton(text=f"{data['name']} | {data['price']}💰", callback_data=f"buycase_{cid}")] for cid, data in CASES_DATA.items()]
    await message.answer("🎰 <b>Выберите сундук для открытия:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp.callback_query(F.data.startswith("buycase_"))
async def open_case_callback(c: types.CallbackQuery):
    cid = c.data.split("_")[1]
    case = CASES_DATA[cid]
    p = get_player(c.from_user.id)
    if p["balance"] < case["price"]: 
        return await c.answer("🚫 Недостаточно монет!", show_alert=True)
    win = random.randint(case["min"], case["max"])
    
    db.table("players").update({"balance": p["balance"] - case["price"] + win}).eq("user_id", c.from_user.id).execute()
    await c.message.edit_text(f"🎰 <b>Открытие {case['name']}...</b>\n💰 Ваш выигрыш составил: <b>{win} монет!</b>", parse_mode="HTML")

@dp.message(F.text.in_({"💎 Продать камни", "/sell"}))
async def sell_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    kb = [[InlineKeyboardButton(text=f"💎 {v['name']} ({p['crystals'].get(k, 0)} шт) — {v['price']}💰", callback_data=f"sell_{k}")] for k, v in CRYSTALS_DATA.items()]
    await message.answer("💎 <b>Рынок драгоценных камней:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp.callback_query(F.data.startswith("sell_"))
async def sell_callback(c: types.CallbackQuery):
    key = c.data.split("_")[1]
    p = get_player(c.from_user.id)
    if p["crystals"].get(key, 0) > 0:
        p["crystals"][key] -= 1
        db.table("players").update({
            "balance": p["balance"] + CRYSTALS_DATA[key]["price"], 
            "crystals": json.dumps(p["crystals"])
        }).eq("user_id", c.from_user.id).execute()
        
        await c.answer(f"✅ Успешно продано!")
        p = get_player(c.from_user.id)
        kb = [[InlineKeyboardButton(text=f"💎 {v['name']} ({p['crystals'].get(k, 0)} шт) — {v['price']}💰", callback_data=f"sell_{k}")] for k, v in CRYSTALS_DATA.items()]
        await c.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    else: 
        await c.answer("🚫 У вас нет этого камня в наличии!", show_alert=True)

@dp.message(F.text.in_({"🛒 Магазин", "/shop"}))
async def shop_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    next_picks = {k: v for k, v in SHOP_PICKS.items() if k > p["pick_lvl"]}
    kb = [[InlineKeyboardButton(text=f"🛒 {v['name']} — {v['price']} 💵", callback_data=f"buy_{k}")] for k, v in next_picks.items()]
    if p["has_drill"] == 0:
        kb.append([InlineKeyboardButton(text="⚙️ Автоматический бур — 500k 💵", callback_data="buy_drill")])
    await message.answer(f"🛒 <b>Магазин инструментов</b>\nУ вас экипирована: {SHOP_PICKS[p['pick_lvl']]['name']}", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb[:10]), parse_mode="HTML")

@dp.callback_query(F.data == "buy_drill")
async def buy_drill_callback(c: types.CallbackQuery):
    p = get_player(c.from_user.id)
    if p["balance"] >= 500000:
        db.table("players").update({"balance": p["balance"] - 500000, "has_drill": 1}).eq("user_id", c.from_user.id).execute()
        await c.message.edit_text("✅ Вы приобрели <b>Автоматический бур</b>!\nТеперь вы получаете +50 монет каждую минуту пассивно.")
    else: 
        await c.answer("🚫 Недостаточно средств!", show_alert=True)

@dp.callback_query(F.data.startswith("buy_"))
async def buy_callback(c: types.CallbackQuery):
    lvl = int(c.data.split("_")[1])
    p = get_player(c.from_user.id)
    if p["balance"] >= SHOP_PICKS[lvl]["price"]:
        inv = p["inventory"]
        if lvl not in inv: 
            inv.append(lvl)
        db.table("players").update({
            "balance": p["balance"] - SHOP_PICKS[lvl]["price"], 
            "pick_lvl": lvl, 
            "inventory": ",".join(map(str, inv))
        }).eq("user_id", c.from_user.id).execute()
        await c.message.edit_text(f"✅ Успешная покупка: {SHOP_PICKS[lvl]['name']}!")
    else: 
        await c.answer("🚫 У вас не хватает монет!", show_alert=True)

@dp.message(F.text.in_({"💳 Баланс", "/balance"}))
async def bal_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    drill = "\n⚙️ Пассивный доход: <b>Активен (+50/мин)</b>" if p["has_drill"] else ""
    await message.answer(f'<tg-emoji emoji-id="{BALANCE_ID}">💳</tg-emoji> Ваши сбережения: <b>{p["balance"]}</b> монет{drill}', parse_mode="HTML")

@dp.message(F.text.in_({"🏆 Топ игроков", "/top"}))
async def top_cmd(message: types.Message):
    res = db.table("players").select("username, balance, user_id").order("balance", desc=True).limit(10).execute()
    text = "🏆 <b>Рейтинг самых богатых шахтеров:</b>\n\n"
    for i, user in enumerate(res.data, 1):
        name = f"@{user['username']}" if user.get('username') else f"Шахтер #{user['user_id']}"
        text += f"{i}. <b>{name}</b> — {user['balance']} 💰\n"
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text.in_({"🎒 Инвентарь", "/inventory"}))
async def inv_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    text = "🎒 <b>Ваше имущество:</b>\n\n"
    for lvl in sorted(p["inventory"]):
        status = " <b>[Экипировано]</b>" if lvl == p["pick_lvl"] else ""
        text += f"• {SHOP_PICKS[lvl]['name']}{status}\n"
    if p["has_drill"]: 
        text += "• ⚙️ Автоматический бур (активен)\n"
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text.in_({"🎁 Бонус", "/bonus"}))
async def bonus_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    now = int(time.time())
    if now - p["last_bonus"] < 86400:
        return await message.answer("🚫 Вы уже забирали ежедневную награду! Приходите завтра.", parse_mode="HTML")
    
    db.table("players").update({"balance": p["balance"] + 2500, "last_bonus": now}).eq("user_id", message.from_user.id).execute()
    await message.answer("🎁 Бонус получен! <b>+2,500 монет</b> зачислены на счет.", parse_mode="HTML")

@dp.message(Command("promo"))
async def promo_cmd(message: types.Message, command: CommandObject):
    if not command.args: 
        return await message.reply("Использование: /promo КОД")
    code = command.args.upper().strip()
    
    res = db.table("promo_codes").select("reward").eq("code", code).execute()
    promo = res.data[0] if res.data else None
    
    if promo:
        p = get_player(message.from_user.id)
        if code in p["used_promos"]: 
            return await message.reply("Вы уже активировали этот промокод!")
        p["used_promos"].append(code)
        
        db.table("players").update({
            "balance": p["balance"] + promo["reward"], 
            "used_promos": ",".join(p["used_promos"])
        }).eq("user_id", message.from_user.id).execute()
        
        await message.reply(f"✅ Успешно! На баланс начислено +{promo['reward']} монет.")
    else: 
        await message.reply("Такого промокода не существует.")

# --- ПАНЕЛЬ АДМИНИСТРАТОРА ---
@dp.message(Command("admin"))
async def admin_start(message: types.Message):
    if message.from_user.id != OWNER_ID: 
        return
    await message.answer("🛠 <b>Панель управления промокодами:</b>\n\nСоздать: `/add КОД НАГРАДА ЧАСЫ` (0 - вечный)\nУдалить: `/del КОД`\nПосмотреть все: `/list`", parse_mode="Markdown")

@dp.message(Command("add"))
async def admin_add(message: types.Message):
    if message.from_user.id != OWNER_ID: 
        return
    try:
        args = message.text.split()
        code, reward, hours = args[1].upper(), int(args[2]), int(args[3])
        expire = "NEVER" if hours == 0 else (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        
        db.table("promo_codes").upsert({"code": code, "reward": reward, "expire_at": expire}).execute()
        await message.answer(f"✅ Промокод <b>{code}</b> на {reward} монет успешно создан!")
    except Exception: 
        await message.answer("Ошибка в формате. Пример: /add REF2026 5000 24")

@dp.message(Command("del"))
async def admin_del(message: types.Message):
    if message.from_user.id != OWNER_ID: 
        return
    try:
        code = message.text.split()[1].upper()
        db.table("promo_codes").delete().eq("code", code).execute()
        await message.answer(f"🗑 Промокод {code} аннулирован.")
    except Exception: 
        pass

@dp.message(Command("list"))
async def admin_list(message: types.Message):
    if message.from_user.id != OWNER_ID: 
        return
    res = db.table("promo_codes").select("*").execute()
    text = "🎫 <b>Список активных кодов:</b>\n" + "\n".join([f"• {p['code']} | Награда: {p['reward']}💰" for p in res.data])
    await message.answer(text if res.data else "Активных промокодов нет.", parse_mode="HTML")

# --- ЗАПУСК БОТА ---
async def main():
    asyncio.create_task(drill_income_task())
    await bot.set_my_commands([
        BotCommand(command="/start", description="Запустить игру"),
        BotCommand(command="/mine", description="Шахта"),
        BotCommand(command="/shop", description="Магазин"),
        BotCommand(command="/balance", description="Баланс"),
        BotCommand(command="/top", description="Рейтинг богачей"),
        BotCommand(command="/admin", description="Панель промокодов")
    ], scope=BotCommandScopeDefault())
    
    print("--- Бот успешно запущен на базе Supabase ---")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
