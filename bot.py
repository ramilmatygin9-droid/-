import telebot
import random
import json
import time
from telebot import types

TOKEN = "8838249295:AAGR3CgnAti-xZwRzpe0duvhdrSMmfw-HaE"

bot = telebot.TeleBot(TOKEN)

try:
    with open("players.json", "r") as f:
        players = json.load(f)
except:
    players = {}


def save():
    with open("players.json", "w") as f:
        json.dump(players, f, indent=4)


def get_player(user):
    uid = str(user.id)

    if uid not in players:
        players[uid] = {
            "name": user.first_name,
            "coins": 0,
            "level": 1,
            "xp": 0,
            "last_bonus": 0
        }
        save()

    return players[uid]


@bot.message_handler(commands=["start"])
def start(message):

    get_player(message.from_user)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(
        types.KeyboardButton("🎮 Играть"),
        types.KeyboardButton("👤 Профиль")
    )

    kb.add(
        types.KeyboardButton("🎁 Бонус"),
        types.KeyboardButton("🏆 Топ")
    )

    bot.send_message(
        message.chat.id,
        "🔥 Добро пожаловать в игру!\n\nЗарабатывай монеты и прокачивай уровень!",
        reply_markup=kb
    )


@bot.message_handler(func=lambda m: m.text=="🎮 Играть")
def game(message):

    p = get_player(message.from_user)

    coins = random.randint(10,50)
    xp = random.randint(5,20)

    p["coins"] += coins
    p["xp"] += xp


    if p["xp"] >= p["level"]*100:
        p["level"] += 1
        p["xp"] = 0
        bot.send_message(
            message.chat.id,
            f"🎉 Новый уровень! Теперь уровень {p['level']}"
        )

    save()

    bot.send_message(
        message.chat.id,
        f"⚔️ Ты сыграл!\n\n+{coins} монет\n+{xp} опыта"
    )


@bot.message_handler(func=lambda m: m.text=="👤 Профиль")
def profile(message):

    p = get_player(message.from_user)

    bot.send_message(
        message.chat.id,
        f"""
👤 Профиль

Игрок: {p['name']}
💰 Монеты: {p['coins']}
⭐ Уровень: {p['level']}
✨ Опыт: {p['xp']}
"""
    )


@bot.message_handler(func=lambda m: m.text=="🎁 Бонус")
def bonus(message):

    p = get_player(message.from_user)

    now = time.time()

    if now - p["last_bonus"] < 86400:
        bot.send_message(
            message.chat.id,
            "⏳ Бонус уже получен. Приходи завтра!"
        )
        return

    reward = 500

    p["coins"] += reward
    p["last_bonus"] = now

    save()

    bot.send_message(
        message.chat.id,
        f"🎁 Ты получил {reward} монет!"
    )


@bot.message_handler(func=lambda m: m.text=="🏆 Топ")
def top(message):

    result = sorted(
        players.values(),
        key=lambda x:x["coins"],
        reverse=True
    )[:10]


    text="🏆 ТОП ИГРОКОВ\n\n"

    for i,p in enumerate(result,1):
        text += f"{i}. {p['name']} — {p['coins']} 💰\n"


    bot.send_message(
        message.chat.id,
        text
    )


bot.infinity_polling()
