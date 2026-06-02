[03.06.2026 1:42] 𐌐𐌀𐌌𐌉𐌋: import os
import random
from telebot import TeleBot, types
from supabase import create_client, Client

# Инициализация переменных окружения из секретов GitHub
TOKEN = os.getenv("8995229149:AAFaZytfsq7EnxMSAaBG-dMsdj9PQEA3SNY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Сюда передается service_role токен

# Подключение к Supabase и Telegram
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = TeleBot(TOKEN)

def get_player(user_id, username):
    # Запрос игрока из базы Supabase
    response = supabase.table("players").select("*").eq("user_id", user_id).execute()
    
    if not response.data:
        # Если игрока еще нет в базе, регистрируем его
        new_player = {
            "user_id": user_id,
            "username": username if username else f"player_{user_id}"
        }
        insert_response = supabase.table("players").insert(new_player).execute()
        return insert_response.data[0]
    
    return response.data[0]

def update_player_data(user_id, update_dict):
    # Функция обновления любых полей игрока
    supabase.table("players").update(update_dict).eq("user_id", user_id).execute()

def main_keyboard():
    # Главное меню кнопок в Telegram
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⛏ Копать руду", "💼 Профиль")
    markup.row("💰 Продать руду", "🏪 Магазин кирок")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    get_player(message.from_user.id, message.from_user.username)
    bot.send_message(
        message.chat.id, 
        "Добро пожаловать в Mines World! ⛏\nДанные сохраняются в облаке Supabase.\n\nКопай шахту, добывай ценные руды, улучшай кирку и зарабатывай игровые деньги! Изредка в шахте можно откопать и чистый кэш!", 
        parse_mode="Markdown", 
        reply_markup=main_keyboard()
    )

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id
    p = get_player(user_id, message.from_user.username)

    if message.text == "⛏ Копать руду":
        luck = random.randint(1, 100)
        lvl = p["pickaxe_lvl"]
        
        # 5% шанс найти чистые деньги в шахте
        if luck <= 5: 
            found_money = random.randint(10, 50) * lvl
            new_money = float(p["money"]) + found_money
            update_player_data(user_id, {"money": new_money})
            bot.reply_to(message, f"🍀 Ого! Ты откопал старый кошелек с деньгами! Получено: **+{found_money} руб.**", parse_mode="Markdown")
            return

        # Логика выпадения руды в зависимости от удачи и уровня кирки
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
        bot.reply_to(message, f"⛏ Ты ударил киркой и добыл: {text} x{amount}!")

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
        # Стоимость ресурсов: Уголь - 1, Железо - 5, Золото - 20, Алмаз - 100
        income = (p["coal"] * 1) + (p["iron"] * 5) + (p["gold"] * 20) + (p["diamond"] * 100)
        
        if income == 0:
            bot.send_message(message.chat.id, "У тебя нет руды на продажу! Сначала сходи в шахту. ⛏")
        else:
            new_money = float(p["money"]) + income
            update_player_data(user_id, {
[03.06.2026 1:42] 𐌐𐌀𐌌𐌉𐌋: "money": new_money,
                "coal": 0,
                "iron": 0,
                "gold": 0,
                "diamond": 0
            })
            bot.send_message(message.chat.id, f"💰 Ты продал всю руду перекупщикам за {income} руб.!", parse_mode="Markdown")

    elif message.text == "🏪 Магазин кирок":
        next_lvl = p["pickaxe_lvl"] + 1
        cost = next_lvl * 150
        
        if float(p["money"]) >= cost:
            new_money = float(p["money"]) - cost
            update_player_data(user_id, {
                "money": new_money,
                "pickaxe_lvl": next_lvl
            })
            bot.send_message(message.chat.id, f"🎉 Поздравляем! Твоя кирка улучшена до {next_lvl} уровня!", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"🏪 Улучшение кирки до {next_lvl} уровня стоит **{cost} руб.**\nУ тебя пока не хватает денег.", parse_mode="Markdown")

if name == "__main__":
    print("Бот Mines World (Supabase Edition) успешно запущен!")
    bot.infinity_polling()
