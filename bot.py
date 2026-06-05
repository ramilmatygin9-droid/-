import os
import sys
import random
import string
import requests
from telebot import TeleBot, types
from supabase import create_client, Client

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    print("❌ ОШИБКА: Не все переменные окружения заданы!")
    sys.exit(1)

bot = TeleBot(TOKEN)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- ФУНКЦИИ ---
def create_email():
    url = 'https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1'
    email = requests.get(url).json()[0]
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return email, password

def get_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⛏ Копать", "💼 Профиль")
    markup.row("📧 Создать почту")
    return markup

# --- ЛОГИКА БОТА ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Добро пожаловать в игру! Выбирай действие:", reply_markup=get_markup())

@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    user_id = message.from_user.id
    
    if message.text == "⛏ Копать":
        res = random.randint(1, 10)
        bot.reply_to(message, f"⛏ Ты накопал {res} единиц руды!")
        
    elif message.text == "💼 Профиль":
        bot.send_message(message.chat.id, f"👤 Твой ID: {user_id}\n💼 Уровень: Новичок")
        
    elif message.text == "📧 Создать почту":
        email, password = create_email()
        bot.send_message(message.chat.id, f"✅ Почта создана:\n\n📧 `{email}`\n🔑 `{password}`", parse_mode="Markdown")

if __name__ == "__main__":
    bot.infinity_polling()
