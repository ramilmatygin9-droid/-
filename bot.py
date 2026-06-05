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
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
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
        new_player = {
            "user_id": user_id, "balance": 0, "pick_lvl": 1, "used_promos": "", 
            "username": username, "last_bonus": 0, "inventory": "1", "crystals": "
