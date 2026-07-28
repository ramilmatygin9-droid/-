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
    conn = sqlite3.connect("heel_game.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS heels (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            size REAL DEFAULT 1.0,
            moisture INTEGER DEFAULT 100,
            tickles INTEGER DEFAULT 100,
            created_at REAL,
            last_watered REAL,
            stage TEXT DEFAULT '🦶 Маленькая пятка'
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Получение или создание пятки для пользователя
def get_or_create_heel(user_id, username):
    conn = sqlite3.connect("heel_game.db")
    cursor = conn.cursor()
    cursor.execute("SELECT size, moisture, tickles, created_at, last_watered, stage FROM heels WHERE user_id = ?", (user_id,))
    heel = cursor.fetchone()
    
    current_time = time.time()
    
    if not heel:
        cursor.execute(
            "INSERT INTO heels (user_id, username, created_at, last_watered) VALUES (?, ?, ?, ?)",
            (user_id, username, current_time, current_time)
        )
        conn.commit()
        heel = (1.0, 100, 100, current_time, current_time, '🦶 Маленькая пятка')
    
    conn.close()
    return heel

# Обновление состояния пятки (рост за 24 часа)
def update_heel_status(user_id):
    conn = sqlite3.connect("heel_game.db")
    cursor = conn.cursor()
    cursor.execute("SELECT size, moisture, tickles, created_at, last_watered, stage FROM heels WHERE user_id = ?", (user_id,))
    heel = cursor.fetchone()
    if not heel:
        conn.close()
        return None
        
    size, moisture, tickles, created_at, last_watered, stage = heel
    current_time = time.time()
    
    # Прошло времени с создания (в часах)
    elapsed_hours = (current_time - created_at) / 3600
    
    # Влажность и щекотка падают со временем
    hours_since_watered = (current_time - last_watered) / 3600
    new_moisture = max(0, int(100 - (hours_since_watered * 12)))
    new_tickles = max(0, int(100 - (hours_since_watered * 10)))
    
    # Рост размера и стадии за 24 часа
    # Базовый размер растет до 45 см за сутки
    current_size = min(45.0, round(1.0 + (elapsed_hours * 1.83), 1))
    
    if elapsed_hours >= 24:
        new_stage = "🦖 Легендарная ГОТИЧЕСКАЯ ПЯТКА-ГОДЗИЛЛА (Выросла!)"
    elif elapsed_hours >= 16:
        new_stage = "🦿 Огромная пятка-батут"
    elif elapsed_hours >= 8:
        new_stage = "👣 Солидная пяточка"
    else:
        new_stage = "🦶 Обычная пятка"
        
    cursor.execute(
        "UPDATE heels SET size = ?, moisture = ?, tickles = ?, stage = ? WHERE user_id = ?",
        (current_size, new_moisture, new_tickles, new_stage, user_id)
    )
    conn.commit()
    
    cursor.execute("SELECT size, moisture, tickles, created_at, last_watered, stage FROM heels WHERE user_id = ?", (user_id,))
    updated_heel = cursor.fetchone()
    conn.close()
    return updated_heel


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🦶 **Добро пожаловать в игру «Вырасти Пятку»!**\n\n"
        "Ваша цель — вырастить гигантскую человеческую пятку за **24 часа**!\n\n"
        "📜 **Как играть:**\n"
        "👣 `/heel` — посмотреть размер и состояние своей пятки\n"
        "💧 Напишите в чат **«полить»** — увлажнить пятку (чтобы не сохла)\n"
        "🖐 Напишите в чат **«пощекотать»** — поднять настроение пятке\n"
        "🏆 `/topheel` — топ самых гигантских пяток сервера"
    )


@dp.message(Command("heel"))
async def cmd_heel(message: Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"
    get_or_create_heel(user_id, username)
    
    heel = update_heel_status(user_id)
    size, moisture, tickles, created_at, last_watered, stage = heel
    
    elapsed_hours = (time.time() - created_at) / 3600
    left_hours = max(0.0, 24 - elapsed_hours)
    
    await message.answer(
        f"📋 **Пятка игрока {username}**\n\n"
        f"Стадия: **{stage}**\n"
        f"📏 Размер: **{size} см**\n"
        f"💧 Влажность кожи: `{moisture}/100`\n"
        f"🤭 Веселье (щекотка): `{tickles}/100`\n"
        f"⏳ До пика эволюции: **{left_hours:.1f} ч.**\n\n"
        "💬 *Напишите в чат «полить» или «пощекотать», чтобы ухаживать за пяткой!*"
    )


# Увлажнение по слову "полить"
@dp.message(F.text.lower() == "полить")
async def water_heel(message: Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"
    get_or_create_heel(user_id, username)
    
    conn = sqlite3.connect("heel_game.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE heels SET moisture = 100, last_watered = ? WHERE user_id = ?", (time.time(), user_id))
    conn.commit()
    conn.close()
    
    await message.answer(f"💧 {username}, вы щедро полили пятку водичкой! Влажность кожи восстановлена до 100%.")


# Щекотка по слову "пощекотать"
@dp.message(F.text.lower() == "пощекотать")
async def tickle_heel(message: Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"
    get_or_create_heel(user_id, username)
    
    conn = sqlite3.connect("heel_game.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE heels SET tickles = 100 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    await message.answer(f"🤭 {username}, вы пощекотали пятку! Она хихикает, уровень веселья на максимуме (100%).")


@dp.message(Command("topheel"))
async def cmd_topheel(message: Message):
    conn = sqlite3.connect("heel_game.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, stage, size FROM heels ORDER BY size DESC LIMIT 10")
    top_players = cursor.fetchall()
    conn.close()
    
    if not top_players:
        await message.answer("🏆 Таблица лидеров пока пуста.")
        return
        
    text = "🏆 **Топ-10 Самых Огромных Пяток:**\n\n"
    for i, (uname, stage, size) in enumerate(top_players, 1):
        text += f"{i}. **{uname}** — {size} см ({stage})\n"
        
    await message.answer(text)


async def main():
    print("Игровой бот 'Вырасти пятку' запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")
