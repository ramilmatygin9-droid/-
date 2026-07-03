import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
# Вставь сюда токен, который тебе выдал @BotFather
BOT_TOKEN = "8156857401:AAFkS4GaCYxGEyFyAwgqsqyah-d9PPNHeH0"

# Твой текст автоответа
REPLY_TEXT = "Привет! Я сейчас занят либо меня сбил камаз 🚛 Мой актуальный юзернейм: @Z_L_0_l"

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Обработка команды /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(REPLY_TEXT)

# Обработка абсолютно любых других текстовых сообщений
@dp.message(F.text)
async def all_messages(message: types.Message):
    await message.answer(REPLY_TEXT)

# Главная функция запуска
async def main():
    print("🤖 Бот-автоответчик по токену запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
