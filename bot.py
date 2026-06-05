import os
import sys
import random
import string
import requests
from telebot import TeleBot, types

# --- БЕЗОПАСНАЯ ЗАГРУЗКА КЛЮЧЕЙ ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("❌ ОШИБКА: Токен не найден в настройках GitHub!")
    sys.exit(1)

bot = TeleBot(TOKEN)

# --- ФУНКЦИИ ПОЧТЫ ---
def generate_random_password(length=12):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def create_email_account():
    url = 'https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1'
    email = requests.get(url).json()[0]
    return email, generate_random_password()

# --- КЛАВИАТУРА ---
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📧 Создать почту")
    return markup

# --- ОБРАБОТЧИК ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Нажми кнопку ниже, чтобы создать временную почту.", reply_markup=main_keyboard())

@bot.message_handler(func=lambda message: message.text == "📧 Создать почту")
def handle_mail(message):
    email, password = create_email_account()
    bot.send_message(
        message.chat.id, 
        f"✅ Почта создана:\n\n📧 `{email}`\n🔑 `{password}`", 
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("🚀 Бот запущен!")
    bot.infinity_polling()
