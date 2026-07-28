import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Ваш токен бота
TOKEN = "8838249295:AAFxtwEj2X9jlisTQlJeUIWgpnJM1OCuUWg"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь для хранения балансов пользователей (стартовый баланс 1000 очков)
user_balances = {}


@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 1000

    await message.answer(
        "🃏 **Добро пожаловать в игру ДЖОКЕР!**\n\n"
        "Правила просты: испытайте удачу и попытайте поймать Джокера.\n"
        "🔹 Напишите в чат: **джокер [сумма]** (например: `джокер 100`)\n\n"
        f"💰 Ваш текущий баланс: **{user_balances[user_id]} очков**\n"
        "Команда /balance — проверить баланс."
    )


@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    user_id = message.from_user.id
    balance = user_balances.get(user_id, 1000)
    user_balances[user_id] = balance
    await message.answer(f"💰 Ваш баланс: **{balance} очков**")


# Обработка текстовых ставок вида "джокер 100"
@dp.message(F.text.lower().startswith("джокер"))
async def play_joker(message: Message):
    user_id = message.from_user.id

    if user_id not in user_balances:
        user_balances[user_id] = 1000

    parts = message.text.split()

    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer(
            "⚠️ Пожалуйста, укажите сумму ставки правильно.\n"
            "Пример: `джокер 100`"
        )
        return

    bet = int(parts[1])
    balance = user_balances[user_id]

    if bet <= 0:
        await message.answer("❌ Ставка должна быть больше нуля!")
        return

    if bet > balance:
        await message.answer(
            f"❌ У вас недостаточно очков! Ваш баланс: **{balance}**"
        )
        return

    # Списываем ставку на время розыгрыша
    user_balances[user_id] -= bet

    # Шансы: 10% — Джокер (х10), 40% — Победа (х2), 50% — Проигрыш
    outcome = random.choices(
        ["joker", "win", "lose"], 
        weights=[10, 40, 50], 
        k=1
    )[0]

    if outcome == "joker":
        win_amount = bet * 10
        user_balances[user_id] += win_amount
        await message.answer(
            f"🃏✨ **ДЖОКЕР! ДЖОКЕР! ДЖОКЕР!** ✨🃏\n"
            f"Невероятная удача! Вы сорвали куш!\n"
            f"🎉 Вы выиграли: **+{win_amount} очков**!\n"
            f"💰 Баланс: {user_balances[user_id]} очков"
        )
    elif outcome == "win":
        win_amount = bet * 2
        user_balances[user_id] += win_amount
        await message.answer(
            f"🎴 Выпала старшая карта.\n"
            f"👍 Вы выиграли х2: **+{win_amount} очков**.\n"
            f"💰 Баланс: {user_balances[user_id]} очков"
        )
    else:
        await message.answer(
            f"❌ К сожалению, выпала пустая карта. Вы проиграли ставку ({bet}).\n"
            f"💰 Баланс: {user_balances[user_id]} очков"
        )


async def main():
    print("Бот 'Джокер' запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")
