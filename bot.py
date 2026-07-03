import os
import asyncio
import logging
import random
import string
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

user_mails = {}

def generate_password(length=12):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def get_main_keyboard():
    kb = [
        [types.KeyboardButton(text="ПОШЕЛ НАХУЙ")]

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "**Привет! Я сейчас занят либо меня сбил камаз 🚛 Мой актуальный юзернейм: @Z_L_0_l",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    
async def main():
    await bot.set_my_commands([BotCommand(command="/start", description="Запуск")], scope=BotCommandScopeDefault())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
 вот пример еще
