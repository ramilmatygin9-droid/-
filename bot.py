import telebot
import random

TOKEN = "8838249295:AAGR3CgnAti-xZwRzpe0duvhdrSMmfw-HaE"

bot = telebot.TeleBot(TOKEN)

players = {}

def get_player(user):
    if user.id not in players:
        players[user.id] = {
            "name": user.first_name,
            "foot": 0,
            "ref": random.randint(100000,999999)
        }
    return players[user.id]

@bot.message_handler(commands=["start"])
def start(message):
    p = get_player(message.from_user)
    bot.reply_to(
        message,
        f"""👋 Привет!

🌱 Выращивай пятку и соревнуйся с друзьями!

Команды:
/grow
/foot
/kiss @username
/slap @username
/steal @username
/ref
/top"""
    )

@bot.message_handler(commands=["grow"])
def grow(message):
    p = get_player(message.from_user)
    p["foot"] += 5
    bot.reply_to(message, f"🌱 Ты вырастил пятку!\nТеперь она {p['foot']}%")

@bot.message_handler(commands=["foot"])
def foot(message):
    p = get_player(message.from_user)
    bot.reply_to(message, f"👣 Размер пятки: {p['foot']}%")

@bot.message_handler(commands=["kiss"])
def kiss(message):
    if len(message.text.split()) < 2:
        bot.reply_to(message, "Использование: /kiss @username")
        return

    bot.reply_to(
        message,
        f"💋 {message.from_user.first_name} поцеловал пятку {message.text.split()[1]} ❤️"
    )

@bot.message_handler(commands=["slap"])
def slap(message):
    if len(message.text.split()) < 2:
        bot.reply_to(message, "Использование: /slap @username")
        return

    bot.reply_to(
        message,
        f"🦶 {message.from_user.first_name} шлёпнул пятку {message.text.split()[1]} 😂"
    )

@bot.message_handler(commands=["steal"])
def steal(message):
    p = get_player(message.from_user)
    value = random.randint(1,3)
    p["foot"] += value

    bot.reply_to(
        message,
        f"🕵️ Ты успешно украл {value}% пятки!\nТеперь у тебя {p['foot']}%"
    )

@bot.message_handler(commands=["ref"])
def ref(message):
    p = get_player(message.from_user)
    bot.reply_to(
        message,
        f"🎁 Твоя рефералка:\nhttps://t.me/YourBot?start={p['ref']}"
    )

@bot.message_handler(commands=["top"])
def top(message):
    if not players:
        bot.reply_to(message, "Пока никто не играл.")
        return

    rating = sorted(players.values(), key=lambda x: x["foot"], reverse=True)

    text = "🏆 ТОП ПЯТОК\n\n"

    for i, player in enumerate(rating[:10], 1):
        text += f"{i}. {player['name']} — {player['foot']}%\n"

    bot.reply_to(message, text)

print("Бот запущен.")
bot.infinity_polling()
