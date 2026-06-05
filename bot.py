import os
import random
from telebot import TeleBot, types
from supabase import create_client

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

bot = TeleBot(TOKEN)
db = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💪 Тренировка", "⚔️ Арена")
    markup.row("🐾 Статус", "🏆 Топ")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # Используем count, чтобы понять, есть ли уже юзер
    existing = db.table("pets").select("user_id").eq("user_id", user_id).execute().data
    if not existing:
        db.table("pets").insert({
            "user_id": user_id, 
            "name": message.from_user.first_name, 
            "str": 10, 
            "gold": 100
        }).execute()
        bot.send_message(message.chat.id, "Добро пожаловать в Pet Arena!", reply_markup=get_markup())
    else:
        bot.send_message(message.chat.id, "Ты уже в игре!", reply_markup=get_markup())

@bot.message_handler(func=lambda message: message.text == "🏆 Топ")
def top_players(message):
    data = db.table("pets").select("name, str").order("str", desc=True).limit(10).execute().data
    if not data:
        return bot.reply_to(message, "Рейтинг пуст.")
    
    res = "\n".join([f"{i+1}. {p['name']} — {p['str']} сил." for i, p in enumerate(data)])
    bot.send_message(message.chat.id, f"🏆 <b>Топ бойцов:</b>\n\n{res}", parse_mode="HTML")

@bot.message_handler(func=lambda message: message.text == "⚔️ Арена")
def arena(message):
    user_id = message.from_user.id
    # Получаем себя
    me = db.table("pets").select("*").eq("user_id", user_id).single().execute().data
    
    # Получаем противников (кроме себя)
    enemies = db.table("pets").select("*").neq("user_id", user_id).execute().data
    
    if not enemies:
        return bot.reply_to(message, "На арене пока пусто...")
    
    enemy = random.choice(enemies)
    
    if me['str'] >= enemy['str']:
        # Исправлено: получаем, прибавляем, записываем
        new_gold = me['gold'] + 50
        db.table("pets").update({"gold": new_gold}).eq("user_id", user_id).execute()
        bot.reply_to(message, f"⚔️ Победа над {enemy['name']}! +50 золота.")
    else:
        bot.reply_to(message, f"💀 Поражение от {enemy['name']}. Потренируйся еще!")

@bot.message_handler(func=lambda message: message.text == "🐾 Статус")
def status(message):
    me = db.table("pets").select("*").eq("user_id", message.from_user.id).single().execute().data
    text = f"🐾 <b>Ваш статус:</b>\n💪 Сила: {me['str']}\n💰 Золото: {me['gold']}"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda message: message.text == "💪 Тренировка")
def train(message):
    # Увеличиваем силу на 1
    me = db.table("pets").select("str").eq("user_id", message.from_user.id).single().execute().data
    db.table("pets").update({"str": me['str'] + 1}).eq("user_id", message.from_user.id).execute()
    bot.reply_to(message, "💪 Тренировка завершена! +1 к силе.")

bot.infinity_polling()
