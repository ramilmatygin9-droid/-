import os
import sys
import random
from telebot import TeleBot, types
from supabase import create_client, Client

# Берем токен из Секретов GitHub репозитория (env-переменная)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Данные твоей базы Supabase остаются здесь
SUPABASE_URL = "https://fuwhycsfqewpjkybdsoi.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ1d"
    "2h5Y3NmcWV3cGpreWJkc29pIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0ODEzNTI"
    "yMCwiZXhwIjoyMDYzNzExMjIwfQ._M9h_0B_E1AAnbB1eS2vLgB9wY-6O6S7x5L0l_X3EwQ"
)

# Жесткая проверка, чтобы бот не молчал, если секрет не задан
if not TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: TELEGRAM_BOT_TOKEN не найден в Secret Repository GitHub!")
    print("💡 Иди в Settings -> Secrets and variables -> Actions и создай секрет TELEGRAM_BOT_TOKEN.")
    sys.exit(1)

try:
    # Инициализация клиентов
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    bot = TeleBot(TOKEN)
    print("✅ Успешное подключение к Telegram через env и базе Supabase!")
except Exception as e:
    print(f"❌ Ошибка инициализации: {e}")
    sys.exit(1)

def get_player(user_id, username):
    try:
        response = supabase.table("players").select("*").eq("user_id", user_id).execute()
        if not response.data:
            new_player = {
                "user_id": user_id,
                "username": username if username else f"player_{user_id}"
            }
            insert_response = supabase.table("players").insert(new_player).execute()
            return insert_response.data[0]
        return response.data[0]
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")
        raise e

def update_player_data(user_id, update_dict):
    supabase.table("players").update(update_dict).eq("user_id", user_id).execute()

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⛏ Копать руду", "💼 Профиль")
    markup.row("💰 Продать руду", "🏪 Магазин кирок")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    try:
        get_player(message.from_user.id, message.from_user.username)
        bot.send_message(
            message.chat.id, 
            "Добро пожаловать в **Mines World**! ⛏\n\nКопай шахту, добывай ценные руды, улучшай кирку и зарабатывай игровые деньги!", 
            parse_mode="Markdown", 
            reply_markup=main_keyboard()
        )
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Ошибка подключения к базе. Проверь вкладку SQL Editor в Supabase.")

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    try:
        user_id = message.from_user.id
        p = get_player(user_id, message.from_user.username)

        if message.text == "⛏ Копать руду":
            luck = random.randint(1, 100)
            lvl = p["pickaxe_lvl"]
            
            if luck <= 5: 
                found_money = random.randint(10, 50) * lvl
                new_money = float(p["money"]) + found_money
                update_player_data(user_id, {"money": new_money})
                bot.reply_to(message, f"🍀 Ты откопал старый кошелек! Получено: **+{found_money} руб.**", parse_mode="Markdown")
                return

            if luck + lvl * 2 > 85:
                ore, text = "diamond", "💎 Алмаз"
            elif luck + lvl * 2 > 65:
                ore, text = "gold", "✨ Золотая руда"
            elif luck + lvl * 2 > 35:
                ore, text = "iron", "⛓ Железная руда"
            else:
                ore, text = "coal", "🪨 Уголь"
                
            amount = random.randint(1, 3) * lvl
            new_amount = p[ore] + amount
            update_player_data(user_id, {ore: new_amount})
            bot.reply_to(message, f"⛏ Ты добыл: {text} x{amount}!")

        elif message.text == "💼 Профиль":
            text = (
                f"👤 Игрок: @{p['username']}\n"
                f"💰 Баланс: **{float(p['money']):.2f} руб.**\n"
                f"🛠 Уровень кирки: **{p['pickaxe_lvl']}**\n\n"
                f"🪨 Уголь: {p['coal']} шт.\n"
                f"⛓ Железо: {p['iron']} шт.\n"
                f"✨ Золото: {p['gold']} шт.\n"
                f"💎 Алмазы: {p['diamond']} шт."
            )
            bot.send_message(message.chat.id, text, parse_mode="Markdown")

        elif message.text == "💰 Продать руду":
            income = (p["coal"] * 1) + (p["iron"] * 5) + (p["gold"] * 20) + (p["diamond"] * 100)
            if income == 0:
                bot.send_message(message.chat.id, "У тебя нет руды на продажу! Сначала сходи в шахту! ⛏")
            else:
                new_money = float(p["money"]) + income
                update_player_data(user_id, {"money": new_money, "coal": 0, "iron": 0, "gold": 0, "diamond": 0})
                bot.send_message(message.chat.id, f"💰 Вся руда продана за **{income} руб.**!", parse_mode="Markdown")

        elif message.text == "🏪 Магазин кирок":
            next_lvl = p["pickaxe_lvl"] + 1
            cost = next_lvl * 150
            if float(p["money"]) >= cost:
                new_money = float(p["money"]) - cost
                update_player_data(user_id, {"money": new_money, "pickaxe_lvl": next_lvl})
                bot.send_message(message.chat.id, f"🎉 Кирка успешно улучшена до **{next_lvl} уровня**!", parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, f"🏪 Улучшение стоит **{cost} руб.**\nНе хватает средств.", parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Ошибка при обработке сообщения: {e}")

if __name__ == "__main__":
    print("🚀 Бот запущен через env и слушает сервера Telegram...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ Ошибка пуллинга: {e}")
