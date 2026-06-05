import os
import random
from telebot import TeleBot, types
from supabase import create_client

# 1. Замени здесь на свои данные, если os.getenv не работает
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

bot = TeleBot(TOKEN)
db = create_client(URL, KEY)

# Функция для создания кнопок
def get_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💪 Тренировка", "⚔️ Арена", "🏆 Топ", "🐾 Статус")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # Проверка, есть ли юзер
    check = db.table("pets").select("user_id").eq("user_id", user_id).execute().data
    if not check:
        db.table("pets").insert({"user_id": user_id, "name": message.from_user.first_name, "str": 10, "gold": 100}).execute()
    bot.send_message(message.chat.id, "Добро пожаловать в Pet Arena!", reply_markup=get_markup())

@bot.message_handler(content_types=['text'])
def main_handler(message):
    text = message.text
    user_id = message.from_user.id

    if text == "💪 Тренировка":
        data = db.table("pets").select("str").eq("user_id", user_id).single().execute().data
        db.table("pets").update({"str": data['str'] + 1}).eq("user_id", user_id).execute()
        bot.reply_to(message, "Ты стал сильнее! +1 к силе.")

    elif text == "⚔️ Арена":
        me = db.table("pets").select("name, str, gold").eq("user_id", user_id).single().execute().data
        enemies = db.table("pets").select("name, str").neq("user_id", user_id).execute().data
        
        if not enemies:
            return bot.reply_to(message, "На арене пусто.")
        
        enemy = random.choice(enemies)
        if me['str'] >= enemy['str']:
            db.table("pets").update({"gold": me['gold'] + 50}).eq("user_id", user_id).execute()
            bot.reply_to(message, f"Победа над {enemy['name']}! +50 золота.")
        else:
            bot.reply_to(message, f"Ты проиграл {enemy['name']}.")

    elif text == "🏆 Топ":
        top = db.table("pets").select("name, str").order("str", desc=True).limit(5).execute().data
        msg = "🏆 Топ бойцов:\n" + "\n".join([f"{i+1}. {p['name']} — {p['str']}" for i, p in enumerate(top)])
        bot.send_message(message.chat.id, msg)

    elif text == "🐾 Статус":
        me = db.table("pets").select("*").eq("user_id", user_id).single().execute().data
        bot.send_message(message.chat.id, f"Имя: {me['name']}\nСила: {me['str']}\nЗолото: {me['gold']}")

# Запуск бота
print("Бот запущен...")
bot.infinity_polling()
