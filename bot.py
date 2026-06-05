import os
import random
from telebot import TeleBot, types
from supabase import create_client

# Инициализация
bot = TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def get_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💪 Тренировка", "⚔️ Арена", "🏆 Топ")
    markup.row("🐾 Статус", "🏪 Магазин", "⚡ Прокачка")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # Используем upsert для создания профиля, если его нет
    supabase.table("pets").upsert({
        "user_id": user_id, 
        "name": message.from_user.first_name, 
        "str": 10, 
        "gold": 100
    }).execute()
    bot.send_message(message.chat.id, "Добро пожаловать в Pet Arena!", reply_markup=get_markup())

@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    user_id = message.from_user.id
    text = message.text

    if text == "🏆 Топ":
        top = supabase.table("pets").select("name, str").order("str", desc=True).limit(10).execute().data
        response = "🏆 <b>Топ бойцов:</b>\n\n" + "\n".join([f"{i}. {p['name']} — {p['str']} силы" for i, p in enumerate(top, 1)])
        bot.send_message(message.chat.id, response, parse_mode="HTML")

    elif text == "⚡ Прокачка":
        # Получаем текущие данные
        user_data = supabase.table("pets").select("str, gold").eq("user_id", user_id).execute().data
        if not user_data:
            return bot.reply_to(message, "Сначала нажми /start")
        
        data = user_data[0]
        if data['gold'] >= 50:
            supabase.table("pets").update({"str": data['str'] + 5, "gold": data['gold'] - 50}).eq("user_id", user_id).execute()
            bot.reply_to(message, "⚡ Сила увеличена на 5! Потрачено 50 золота.")
        else:
            bot.reply_to(message, "❌ Недостаточно золота.")

    elif text == "⚔️ Арена":
        # Исправлено: выбор противника по user_id
        all_players = supabase.table("pets").select("user_id, name, str").neq("user_id", user_id).execute().data
        if not all_players:
            return bot.reply_to(message, "Пока нет других игроков для боя.")
        
        enemy = random.choice(all_players)
        my_data = supabase.table("pets").select("str, gold").eq("user_id", user_id).execute().data[0]
        
        if my_data['str'] >= enemy['str']:
            new_gold = my_data['gold'] + 100
            supabase.table("pets").update({"gold": new_gold}).eq("user_id", user_id).execute()
            bot.reply_to(message, f"⚔️ Победа над {enemy['name']}! +100 золота.")
        else:
            bot.reply_to(message, f"💀 Ты проиграл бой против {enemy['name']}.")

bot.polling(none_stop=True)
