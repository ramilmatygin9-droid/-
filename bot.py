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

# Настройка логирования
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
raw_owner_id = os.getenv("OWNER_ID", "0")
OWNER_ID = int(raw_owner_id.strip()) if raw_owner_id.strip().isdigit() else 0

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_FILE = "database.json"

# Инициализация локальной БД
def load_db():
    if not os.path.exists(DB_FILE):
        return {"players": {}, "promo_codes": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"players": {}, "promo_codes": {}}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_player(user_id, username=None):
    db_data = load_db()
    uid = str(user_id)
    
    if uid not in db_data["players"]:
        db_data["players"][uid] = {
            "balance": 1000,  # Даем стартовый капитал!
            "pick_lvl": 1,
            "used_promos": [],
            "username": username or f"Miner_{uid[:5]}",
            "last_bonus": 0,
            "inventory": [1],
            "crystals": {"Common": 0, "Rare": 0, "SuperRare": 0},
            "has_drill": 0
        }
        save_db(db_data)
    
    # Обновляем юзернейм если изменился
    if username and db_data["players"][uid].get("username") != username:
        db_data["players"][uid]["username"] = username
        save_db(db_data)
        
    return db_data["players"][uid]

def update_player(user_id, updated_fields):
    db_data = load_db()
    uid = str(user_id)
    if uid in db_data["players"]:
        db_data["players"][uid].update(updated_fields)
        save_db(db_data)

# Константы игры
CRYSTALS_DATA = {
    "Common": {"name": "Обычный кристалл", "price": 1000},
    "Rare": {"name": "Редкий кристалл", "price": 2500},
    "SuperRare": {"name": "Сверхредкий кристалл", "price": 5000}
}

CASES_DATA = {
    "wood": {"name": "📦 Деревянный кейс", "price": 5000, "min": 1000, "max": 12000},
    "iron": {"name": "🎁 Железный кейс", "price": 25000, "min": 5000, "max": 60000},
    "gold": {"name": "💎 Золотой кейс", "price": 100000, "min": 25000, "max": 250000}
}

SHOP_PICKS = {
    1: {"name": "Деревянная кирка", "price": 0, "mult": 1.0},
    2: {"name": "Каменная кирка", "price": 5000, "mult": 1.5},
    3: {"name": "Железная кирка", "price": 15000, "mult": 2.5},
    4: {"name": "Золотая кирка", "price": 50000, "mult": 5.0},
    5: {"name": "Алмазная кирка", "price": 150000, "mult": 10.0}
}

active_miners = set()

def get_main_keyboard():
    kb = [
        [types.KeyboardButton(text="⛏ Шахта"), types.KeyboardButton(text="🛒 Магазин")],
        [types.KeyboardButton(text="💳 Баланс"), types.KeyboardButton(text="🎒 Инвентарь")],
        [types.KeyboardButton(text="🎰 Кейсы"), types.KeyboardButton(text="💎 Продать камни")],
        [types.KeyboardButton(text="🏆 Топ игроков"), types.KeyboardButton(text="🎁 Бонус")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(Command("start"))
async def main_start(message: types.Message):
    get_player(message.from_user.id, message.from_user.username)
    start_text = (
        f"<b>─── 〈 ⛏ MINER WORLD 〉 ───</b>\n\n"
        f"👋 Привет, <b>{message.from_user.full_name}</b>!\n"
        f"Добро пожаловать в автономный симулятор шахтера.\n\n"
        f"Вся база сохраняется автоматически. Используй меню для игры!"
    )
    await message.answer(start_text, reply_markup=get_main_keyboard(), parse_mode="HTML")

@dp.message(F.text == "⛏ Шахта")
async def main_mine(message: types.Message):
    user_id = message.from_user.id
    if user_id in active_miners:
        return await message.reply('🚫 <b>Вы уже копаете в шахте!</b>', parse_mode="HTML")
    
    active_miners.add(user_id)
    p = get_player(user_id, message.from_user.username)
    
    status_msg = await message.answer("⛏ <b>Вы спустились в шахту...</b>\n\n⏳ Машете киркой, ждите ресурсов.", parse_mode="HTML")
    await asyncio.sleep(random.randint(3, 5))
    
    base_reward = random.randint(150, 400)
    is_crit = random.random() < 0.15
    crit_mult = 2 if is_crit else 1
    reward = int(base_reward * SHOP_PICKS[p["pick_lvl"]]["mult"] * crit_mult)
    
    crystal_msg = ""
    if random.random() < 0.30:
        c_key = random.choice(list(CRYSTALS_DATA.keys()))
        p["crystals"][c_key] = p["crystals"].get(c_key, 0) + 1
        crystal_msg = f'\n✨ Находка: 💎 <b>{CRYSTALS_DATA[c_key]["name"]}</b>!'

    p["balance"] += reward
    update_player(user_id, {"balance": p["balance"], "crystals": p["crystals"]})
    
    active_miners.remove(user_id)
    crit_text = "<b>⚡ КРИТИЧЕСКИЙ УДАР (X2)!</b>\n" if is_crit else ""
    try: await status_msg.delete() 
    except Exception: pass
    
    await message.answer(f'💰 <b>Успешная добыча!</b>\n{crit_text}+ {reward} монет{crystal_msg}', parse_mode="HTML")

@dp.message(F.text == "🎰 Кейсы")
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
    p["balance"] = p["balance"] - case["price"] + win
    update_player(c.from_user.id, {"balance": p["balance"]})
    
    await c.message.edit_text(f"🎰 <b>Открытие {case['name']}...</b>\n💰 Выигрыш: <b>{win} монет!</b>", parse_mode="HTML")

@dp.message(F.text == "💎 Продать камни")
async def sell_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    kb = [[InlineKeyboardButton(text=f"💎 {v['name']} ({p['crystals'].get(k, 0)} шт) — {v['price']}💰", callback_data=f"sell_{k}")] for k, v in CRYSTALS_DATA.items()]
    await message.answer("💎 <b>Рыночная лавка:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp.callback_query(F.data.startswith("sell_"))
async def sell_callback(c: types.CallbackQuery):
    key = c.data.split("_")[1]
    p = get_player(c.from_user.id)
    if p["crystals"].get(key, 0) > 0:
        p["crystals"][key] -= 1
        p["balance"] += CRYSTALS_DATA[key]["price"]
        update_player(c.from_user.id, {"balance": p["balance"], "crystals": p["crystals"]})
        
        await c.answer("✅ Успешно продано!")
        p = get_player(c.from_user.id)
        kb = [[InlineKeyboardButton(text=f"💎 {v['name']} ({p['crystals'].get(k, 0)} шт) — {v['price']}💰", callback_data=f"sell_{k}")] for k, v in CRYSTALS_DATA.items()]
        await c.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    else: 
        await c.answer("🚫 У вас нет этого камня!", show_alert=True)

@dp.message(F.text == "🛒 Магазин")
async def shop_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    next_picks = {k: v for k, v in SHOP_PICKS.items() if k > p["pick_lvl"]}
    kb = [[InlineKeyboardButton(text=f"🛒 {v['name']} — {v['price']} 💵", callback_data=f"buy_{k}")] for k, v in next_picks.items()]
    if p.get("has_drill", 0) == 0:
        kb.append([InlineKeyboardButton(text="⚙️ Авто-бур — 100k 💵", callback_data="buy_drill")])
    await message.answer(f"🛒 <b>Магазин кирок</b>\nВаша кирка: {SHOP_PICKS[p['pick_lvl']]['name']}", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp.callback_query(F.data == "buy_drill")
async def buy_drill_callback(c: types.CallbackQuery):
    p = get_player(c.from_user.id)
    if p["balance"] >= 100000:
        update_player(c.from_user.id, {"balance": p["balance"] - 100000, "has_drill": 1})
        await c.message.edit_text("✅ Вы купили <b>Автоматический бур</b>!\nКаждую минуту он дает +50 монет пассивно.")
    else: 
        await c.answer("🚫 Недостаточно монет!", show_alert=True)

@dp.callback_query(F.data.startswith("buy_"))
async def buy_callback(c: types.CallbackQuery):
    lvl = int(c.data.split("_")[1])
    p = get_player(c.from_user.id)
    if p["balance"] >= SHOP_PICKS[lvl]["price"]:
        inv = p["inventory"]
        if lvl not in inv: inv.append(lvl)
        update_player(c.from_user.id, {
            "balance": p["balance"] - SHOP_PICKS[lvl]["price"], 
            "pick_lvl": lvl, 
            "inventory": inv
        })
        await c.message.edit_text(f"✅ Успешно куплена: {SHOP_PICKS[lvl]['name']}!")
    else: 
        await c.answer("🚫 Не хватает монет!", show_alert=True)

@dp.message(F.text == "💳 Баланс")
async def bal_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    drill = "\n⚙️ Авто-бур: <b>Активен (+50/мин)</b>" if p.get("has_drill") else ""
    await message.answer(f'💳 Кошелек: <b>{p["balance"]}</b> монет{drill}', parse_mode="HTML")

@dp.message(F.text == "🏆 Топ игроков")
async def top_cmd(message: types.Message):
    db_data = load_db()
    players = db_data["players"]
    sorted_players = sorted(players.items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
    
    text = "🏆 <b>Рейтинг богатых шахтеров:</b>\n\n"
    for i, (uid, data) in enumerate(sorted_players, 1):
        text += f"{i}. <b>@{data['username']}</b> — {data['balance']} 💰\n"
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "🎒 Инвентарь")
async def inv_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    text = "🎒 <b>Ваш рюкзак:</b>\n\n"
    for lvl in sorted(p["inventory"]):
        status = " <b>[Экипировано]</b>" if lvl == p["pick_lvl"] else ""
        text += f"• {SHOP_PICKS[lvl]['name']}{status}\n"
    if p.get("has_drill"): 
        text += "• ⚙️ Автоматический бур\n"
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "🎁 Бонус")
async def bonus_cmd(message: types.Message):
    p = get_player(message.from_user.id)
    now = int(time.time())
    if now - p["last_bonus"] < 86400:
        return await message.answer("🚫 Награда уже получена! Возвращайтесь завтра.")
    
    update_player(message.from_user.id, {"balance": p["balance"] + 2500, "last_bonus": now})
    await message.answer("🎁 Ежедневный бонус взят! <b>+2,500 монет</b>.")

@dp.message(Command("promo"))
async def promo_cmd(message: types.Message, command: CommandObject):
    if not command.args: return await message.reply("Использование: /promo КОД")
    code = command.args.upper().strip()
    
    db_data = load_db()
    if code in db_data["promo_codes"]:
        promo = db_data["promo_codes"][code]
        p = get_player(message.from_user.id)
        
        if code in p["used_promos"]: 
            return await message.reply("Вы уже активировали этот код!")
        
        p["used_promos"].append(code)
        p["balance"] += promo["reward"]
        
        update_player(message.from_user.id, {"balance": p["balance"], "used_promos": p["used_promos"]})
        await message.reply(f"✅ Активировано! Начислено +{promo['reward']} монет.")
    else:
        await message.reply("Такого промокода нет.")

# --- АДМИН-КОМАНДЫ ДЛЯ ПРОМОКОДОВ ---
@dp.message(Command("admin"))
async def admin_start(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    await message.answer("🛠 <b>Админ-панель:</b>\n\nСоздать промо: `/add КОД НАГРАДА`\nПосмотреть все: `/list`", parse_mode="Markdown")

@dp.message(Command("add"))
async def admin_add(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        args = message.text.split()
        code, reward = args[1].upper(), int(args[2])
        db_data = load_db()
        db_data["promo_codes"][code] = {"reward": reward}
        save_db(db_data)
        await message.answer(f"✅ Промокод <b>{code}</b> на {reward} монет создан!")
    except Exception:
        await message.answer("Формат: /add КОД НАГРАДА")

@dp.message(Command("list"))
async def admin_list(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    db_data = load_db()
    text = "🎫 <b>Список кодов:</b>\n" + "\n".join([f"• {k} — {v['reward']}💰" for k, v in db_data["promo_codes"].items()])
    await message.answer(text if db_data["promo_codes"] else "Кодов нет.", parse_mode="HTML")

async def drill_income_task():
    while True:
        await asyncio.sleep(60)
        try:
            db_data = load_db()
            for uid, data in db_data["players"].items():
                if data.get("has_drill", 0) == 1:
                    data["balance"] += 50
            save_db(db_data)
        except Exception:
            pass

async def main():
    asyncio.create_task(drill_income_task())
    await bot.set_my_commands([
        BotCommand(command="/start", description="Начать играть"),
        BotCommand(command="/promo", description="Активировать промокод"),
        BotCommand(command="/admin", description="Панель создателя")
    ], scope=BotCommandScopeDefault())
    print("--- Локальный автономный бот запущен ---")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
