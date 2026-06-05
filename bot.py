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
    print("❌ ОШИБКА: Секреты (Tokens/URL) не найдены!")
    sys.exit(1)

try:
    bot = TeleBot(TOKEN)
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Бот инициализирован успешно!")
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
    sys.exit(1)

# --- ФУНКЦИИ ---
def create_email():
    url = 'https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1'
    try:
        email = requests.get(url).json()[0]
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        return email, password
    except:
        return "Ошибка API", "Попробуй позже"

def get_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⛏ Копать", "💼 Профиль")
    markup.row("📧 Создать почту")
    return markup

# --- ОБРАБОТЧИКИ ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # Проверка пользователя в базе
    resp = supabase.table("players").select("*").eq("user_id", user_id).execute()
    if not resp.data:
        supabase.table("players").insert({"user_id": user_id, "balance": 0, "level": 1}).execute()
    
    bot.send_message(message.chat.id, "Добро пожаловать в игру!", reply_markup=get_markup())

@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    user_id = message.from_user.id
    
    if message.text == "⛏ Копать":
        res = random.randint(1, 10)
        supabase.table("players").update({"balance": "balance + " + str(res)}).eq("user_id", user_id).execute()
        bot.reply_to(message, f"⛏ Ты накопал {res} руды!")
        
    elif message.text == "💼 Профиль":
        resp = supabase.table("players").select("*").eq("user_id", user_id).execute()
        p = resp.data[0]
        bot.send_message(message.chat.id, f"👤 ID: {p['user_id']}\n💰 Баланс: {p['balance']}\n💼 Уровень: {p['level']}")
        
    elif message.text == "📧 Создать почту":
        email, password = create_email()
        bot.send_message(message.chat.id, f"✅ Почта создана:\n\n📧 `{email}`\n🔑 `{password}`", parse_mode="Markdown")

if __name__ == "__main__":
    bot.infinity_polling()
