import os
import asyncio
import logging
import random
import string
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault

logging.basicConfig(level=logging.INFO)

# Токен берется из переменных окружения ОС или можешь вставить строкой: TOKEN = "ТВОЙ_ТОКЕН"
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Текст автоответа
REPLY_TEXT = "**Привет! Я сейчас занят либо меня сбил камаз 🚛 Мой актуальный юзернейм: @Z_L_0_l**"

def get_main_keyboard():
    kb = [
        [types.KeyboardButton(text="ПОШЕЛ НАХУЙ")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# Ответ на команду /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        REPLY_TEXT,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# Ответ на нажатие кнопки или любое другое текстовое сообщение
@dp.message(F.text)
async def all_msg(message: types.Message):
    await message.answer(
        REPLY_TEXT,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
    
async def main():
    await bot.set_my_commands([BotCommand(command="/start", description="Запуск")], scope=BotCommandScopeDefault())
    print("🤖 Бот про КАМАЗ запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
