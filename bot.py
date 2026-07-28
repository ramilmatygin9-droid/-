import asyncio
import logging
import sqlite3
import time
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Ваш токен бота
TOKEN = "8838249295:AAFxtwEj2X9jlisTQlJeUIWgpnJM1OCuUWg"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Инициализация базы данных SQLite
def init_db():
    conn = sqlite3.connect("pets.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            hunger INTEGER DEFAULT 100,
            happiness INTEGER DEFAULT 100,
            created_at REAL,
            last_fed REAL,
            stage TEXT DEFAULT '🥚 Яйцо'
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Функция получения или создания питомца
def get_or_create_pet(user_id, username):
    conn = sqlite3.connect("pets.db")
    cursor = conn.cursor()
    cursor.execute("SELECT hunger, happiness, created_at, last_fed, stage FROM pets WHERE user_id = ?", (user_id,))
    pet = cursor.fetchone()
    
    current_time = time.time()
    
    if not pet:
        # Создаем нового питомца (Яйцо)
        cursor.execute(
            "INSERT INTO pets (user_id, username, created_at, last_fed) VALUES (?, ?, ?, ?)",
            (user_id, username, current_time, current_time)
        )
        conn.commit()
        pet = (100, 100, current_time, current_time, '🥚 Яйцо')
    
    conn.close()
    return pet

# Обновление состояния питомца (рост за 24 часа)
def update_pet_status(user_id):
    conn = sqlite3.connect("pets.db")
    cursor = conn.cursor()
    cursor.execute("SELECT hunger, happiness, created_at, last_fed, stage FROM pets WHERE user_id = ?", (user_id,))
    pet = cursor.fetchone()
    if not pet:
        conn.close()
        return None
        
    hunger, happiness, created_at, last_fed, stage = pet
    current_time = time.time()
    
    # Прошло времени с момента создания (в секундах)
    elapsed_total = current_time - created_at
    hours_passed = elapsed_total / 3600
    
    # Естественное уменьшение сытости и счастья со временем (раз в час падает на 5)
    hours_since_fed = (current_time - last_fed) / 3600
    new_hunger = max(0, int(100 - (hours_since_fed * 10)))
    new_happiness = max(0, int(100 - (hours_since_fed * 8)))
    
    # Стадии роста за 24 часа
    if hours_passed >= 24:
        new_stage = "🐉 Дракон (Вырос!)"
    elif hours_passed >= 16:
        new_stage = "🦖 Подросток"
    elif hours_passed >= 8:
        new_stage = "🐣 Малыш"
    else:
        new_stage = "🥚 Яйцо"
        
    cursor.execute(
        "UPDATE pets SET hunger = ?, happiness = ?, stage = ? WHERE user_id = ?",
        (new_hunger, new_happiness, new_stage, user_id)
    )
    conn.commit()
    
    cursor.execute("SELECT hunger, happiness, created_at, last_fed, stage FROM pets WHERE user_id = ?", (user_id,))
    updated_pet = cursor.fetchone()
    conn.close()
    return updated_pet


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🐾 **Добро пожаловать в игру «Питомник»!**\n\n"
        "Вырастите своего питомца из яйца в могущественного дракона за **24 часа**!\n\n"
        "📜 **Команды игры:**\n"
        "🥚 `/pet` — посмотреть состояние питомца\n"
        " корм — покормить питомца (напишите в чат слово `корм`)\n"
        " поиграть — развлечь питомца (напишите `поиграть`)\n"
        "🏆 `/top` — таблица лучших питомцев"
    )


@dp.message(Command("pet"))
async def cmd_pet(message: Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"
    get_or_create_pet(user_id, username)
    
    pet = update_pet_status(user_id)
    hunger, happiness, created_at, last_fed, stage = pet
    
    # Считаем оставшееся время до 24 часов
    elapsed_hours = (time.time() - created_at) / 3600
    left_hours = max(0.0, 24 - elapsed_hours)
    
    await message.answer(
        f"📋 **Питомец игрока {username}**\n\n"
        f"Стадия: **{stage}**\n"
        f"🍗 Сытость: `{hunger}/100`\n"
        f"💖 Счастье: `{happiness}/100`\n"
        f"⏳ До полного взросления: **{left_hours:.1f} ч.**\n\n"
        "💬 *Напишите в чат «корм» или «поиграть», чтобы ухаживать за ним!*"
    )


# Кормежка по слову "корм" в чате
@dp.message(F.text.lower() == "корм")
async def feed_pet(message: Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"
    get_or_create_pet(user_id, username)
    
    conn = sqlite3.connect("pets.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE pets SET hunger = 100, last_fed = ? WHERE user_id = ?", (time.time(), user_id))
    conn.commit()
    conn.close()
    
    await message.answer(f"🍖 {username}, вы покормили питомца! Сытость восстановлена до 100%.")


# Игра с питомцем по слову "поиграть"
@dp.message(F.text.lower() == "поиграть")
async def play_pet(message: Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"
    get_or_create_pet(user_id, username)
    
    conn = sqlite3.connect("pets.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE pets SET happiness = 100 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    await message.answer(f"🎾 {username}, вы поиграли с питомцем! Счастье на максимуме (100%).")


@dp.message(Command("top"))
async def cmd_top(message: Message):
    conn = sqlite3.connect("pets.db")
    cursor = conn.cursor()
    # Топ составляется по времени создания (кто дольше выращивает) и сумме сытости+счастья
    cursor.execute("SELECT username, stage, (hunger + happiness) as score FROM pets ORDER BY created_at ASC LIMIT 10")
    top_players = cursor.fetchall()
    conn.close()
    
    if not top_players:
        await message.answer("🏆 Таблица лидеров пока пуста.")
        return
        
    text = "🏆 **Топ-10 Питомцев:**\n\n"
    for i, (uname, stage, score) in enumerate(top_players, 1):
        text += f"{i}. **{uname}** — {stage} (Очки ухода: {score})\n"
        
    await message.answer(text)


async def main():
    print("Игровой бот 'Питомник' запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")
