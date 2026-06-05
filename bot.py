import os
import sys
import random
import string
import requests
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from supabase import create_client, Client

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    print("❌ ОШИБКА: Не все переменные окружения заданы!")
    sys.exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher()
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- ФУНКЦИИ ---
def create_email():
    url = 'https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1'
    email = requests.get(url).json()[0]
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return email, password

def get_markup():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="⛏ Копать"), KeyboardButton(text="💼 Профиль")],
        [KeyboardButton(text="📧 Создать почту")]
    ], resize_keyboard=True)

# --- ЛОГИКА ---
@dp.message(Command("start"))
async def start(message: types.Message):
    # Проверка игрока в Supabase
    user_id = message.from_user.id
    resp = supabase.table("players").select("*").eq("user_id", user_id).execute()
    if not resp.data:
        supabase.table("players").insert({"user_id": user_id, "balance": 0, "level": 1}).execute()
    
    await message.answer("Добро пожаловать в игру!", reply_markup=get_markup())

@dp.message(F.text == "⛏ Копать")
async def mine(message: types.Message):
    res = random.randint(1, 10)
    # Обновление баланса в Supabase
    supabase.table("players").update({"balance": F.expr("balance + " + str(res))}).eq("user_id", message.from_user.id).execute()
    await message.answer(f"⛏ Ты накопал {res} руды!")

@dp.message(F.text == "💼 Профиль")
async def profile(message: types.Message):
    resp = supabase.table("players").select("*").eq("user_id", message.from_user.id).execute()
    p = resp.data[0]
    await message.answer(f"👤 Твой ID: {p['user_id']}\n💰 Баланс: {p['balance']}\n💼 Уровень: {p['level']}")

@dp.message(F.text == "📧 Создать почту")
async def mail(message: types.Message):
    email, password = create_email()
    await message.answer(f"✅ Почта создана:\n\n📧 `{email}`\n🔑 `{password}`", parse_mode="Markdown")

async def main():
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
