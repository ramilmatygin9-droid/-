import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Укажите ваш токен, полученный от @BotFather
TOKEN = "8838249295:AAGR3CgnAti-xZwRzpe0duvhdrSMmfw-HaE"

# Инициализируем бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь для хранения загаданных чисел игроков: {user_id: target_number}
user_games = {}


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🎮 Привет! Добро пожаловать в игру **«Угадай число»**!\n\n"
        "Я загадал число от **1 до 100**. Попробуй угадать его!\n"
        "Просто отправь мне число в чат.\n\n"
        "Если захочешь начать новую игру, отправь /game"
    )


# Хэндлер на команду /game (начало/перезапуск игры)
@dp.message(Command("game"))
async def cmd_game(message: Message):
    user_id = message.from_user.id
    # Загадываем новое число для пользователя
    user_games[user_id] = random.randint(1, 100)

    await message.answer(
        "🎲 Я загадал новое число от 1 до 100. Жду твой вариант!"
    )


# Логика обработки ответов (угадывание числа)
@dp.message(F.text)
async def check_number(message: Message):
    user_id = message.from_user.id

    # Проверяем, играет ли пользователь (есть ли у него загаданное число)
    if user_id not in user_games:
        # Если игра не начиналась, автоматически запускаем её
        user_games[user_id] = random.randint(1, 100)
        await message.answer(
            "⚠️ Ты еще не начал игру, но я уже загадал число от 1 до 100! Попробуй угадать:"
        )
        return

    # Проверяем, является ли введенный текст числом
    if not message.text.isdigit():
        await message.answer(
            "❌ Пожалуйста, введи **целое число** от 1 до 100."
        )
        return

    guess = int(message.text)
    target = user_games[user_id]

    # Сравниваем число пользователя с загаданным
    if guess < target:
        await message.answer("📈 Мое число **больше**! Попробуй еще раз.")
    elif guess > target:
        await message.answer("📉 Мое число **меньше**! Попробуй еще раз.")
    else:
        # Пользователь угадал!
        await message.answer(
            f"🎉 Поздравляю! Ты угадал число **{target}**!\n\n"
            "Хочешь сыграть еще? Просто отправь /game"
        )
        # Сбрасываем игру, чтобы загадать новое число на следующий раз
        del user_games[user_id]


# Главная функция запуска
async def main():
    print("Игровой бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")
