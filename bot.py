import os
import telebot
from supabase import create_client

# Убедись, что переменные среды установлены в системе
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

bot = telebot.TeleBot(TOKEN)
db = create_client(URL, KEY)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Бот работает! Привет.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    # Тест: просто отвечает тем же текстом
    bot.reply_to(message, f"Ты написал: {message.text}")

print("--- Бот успешно запущен и слушает сообщения ---")
bot.infinity_polling()
