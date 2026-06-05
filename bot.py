import os
import sys
import random
from telebot import TeleBot, types
from supabase import create_client, Client

# --- БЕЗОПАСНАЯ ЗАГРУЗКА КЛЮЧЕЙ ---
# Эти функции ищут переменные в настройках GitHub (Secrets)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Проверка на наличие ключей
if not TOKEN or not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: Секреты не найдены!")
    sys.exit(1)

try:
    # Инициализация клиентов
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    bot = TeleBot(TOKEN)
    print("✅ Успешное подключение к базе данных и Telegram!")
except Exception as e:
    print(f"❌ Ошибка инициализации: {e}")
    sys.exit(1)

def get_player(user_id, username):
    try:
        response = supabase.table("players").select("*").eq("user_id", user_id).execute()
        if not response.data:
            new_player = {
                "user_id": user_id,
                "username": username if username else f"player_{user_id}",
                "money": 0,
                "pickaxe_lvl": 1,
                "coal": 0, "iron": 0, "gold": 0, "diamond": 0
            }
            supabase.table("players").insert(new_player).execute()
            return new_player
        return response.data[0]
    except Exception as e:
        print(f"❌ Ошибка DB: {e}")
        return None

def update_player_data(user_id, update_dict):
    supabase.table("players").update(update_dict).eq("user_id", user_id).execute()

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⛏ Копать руду", "💼 Профиль")
    markup.row("💰 Продать руду", "🏪 Магазин кирок")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    get_player(message.from_user.id, message.from_user.username)
    bot.send_message(
        message.chat.id, 
        "Добро пожаловать в **Mines World**! ⛏", 
        parse_mode="Markdown", 
        reply_markup=main_keyboard()
    )

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id
    p = get_player(user_id, message.from_user.username)
    if not p: return

    if message.text == "⛏ Копать руду":
        luck = random.randint(1, 100)
        lvl = p["pickaxe_lvl"]
        if luck <= 5: 
            found = random.randint(10, 50) * lvl
            update_player_data(user_id, {"money": float(p["money"]) + found})
            bot.reply_to(message, f"🍀 Нашел кошелек! +{found} руб.")
            return
        
        if luck + lvl * 2 > 85: ore, text = "diamond", "💎 Алмаз"
        elif luck + lvl * 2 > 65: ore, text = "gold", "✨ Золото"
        elif luck + lvl * 2 > 35: ore, text = "iron", "⛓ Железо"
        else: ore, text = "coal", "🪨 Уголь"
        
        amount = random.randint(1, 3) * lvl
        update_player_data(user_id, {ore: p[ore] + amount})
        bot.reply_to(message, f"⛏ Добыто: {text} x{amount}!")

    elif message.text == "💼 Профиль":
        text = (f"👤 {p['username']}\n💰 Баланс: {float(p['money']):.2f} руб.\n"
                f"🛠 Уровень кирки: {p['pickaxe_lvl']}\n🪨 Уголь: {p['coal']}\n"
                f"⛓ Железо: {p['iron']}\n✨ Золото: {p['gold']}\n💎 Алмазы: {p['diamond']}")
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

    elif message.text == "💰 Продать руду":
        income = (p["coal"]*1) + (p["iron"]*5) + (p["gold"]*20) + (p["diamond"]*100)
        if income == 0: bot.send_message(message.chat.id, "Нет руды!")
        else:
            update_player_data(user_id, {"money": float(p["money"])+income, "coal":0, "iron":0, "gold":0, "diamond":0})
            bot.send_message(message.chat.id, f"💰 Продано за {income} руб.!")

    elif message.text == "🏪 Магазин кирок":
        next_lvl = p["pickaxe_lvl"] + 1
        cost = next_lvl * 150
        if float(p["money"]) >= cost:
            update_player_data(user_id, {"money": float(p["money"]) - cost, "pickaxe_lvl": next_lvl})
            bot.send_message(message.chat.id, f"🎉 Кирка {next_lvl} уровня!")
        else:
            bot.send_message(message.chat.id, f"Не хватает! Нужно {cost} руб.")

if __name__ == "__main__":
    bot.infinity_polling()
