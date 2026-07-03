import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- НАСТРОЙКА ---
# Замени этот ноль на свой настоящий цифровой ID (например, 123456789)
MY_TELEGRAM_ID = 8462392581 
# ------------------

REPLY_TEXT = "**Привет! Я сейчас занят либо меня сбил камаз 🚛 Мой актуальный юзернейм: @Z_L_0_l**"

def get_main_keyboard():
    kb = [
        [types.KeyboardButton(text="ПОШЕЛ НАХУЙ")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# Ответ на команду /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    # Выводим ID в консоль, чтобы ты мог его узнать при первом запуске
    print(f"Сообщение от пользователя с ID: {message.from_user.id}")
    
    # Если написал ТЫ — бот ничего не делает и завершает работу функции
    if message.from_user.id == MY_TELEGRAM_ID:
        return 
        
    await message.answer(
        REPLY_TEXT,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# Ответ на нажатие кнопки или любое другое текстовое сообщение
@dp.message(F.text)
async def all_msg(message: types.Message):
    print(f"Сообщение от пользователя с ID: {message.from_user.id}")
    
    # Если написал ТЫ — бот молчит
    if message.from_user.id == MY_TELEGRAM_ID:
        return 

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
