import os
from dotenv import load_dotenv

TOKEN = os.getenv("8838249295:AAGR3CgnAti-xZwRzpe0duvhdrSMmfw-HaE")

bot = telebot.TeleBot(TOKEN)

# База игроков: ключ — user.id, значение — словарик с данными
players = {}
# Словарь для быстрого поиска id по реферальному коду: ref_code -> user_id
ref_codes = {}
# Словарь для поиска id по username (в нижнем регистре): username -> user_id
username_to_id = {}


def get_player(user):
    # Обновляем юзернейм в словаре поиска
    if user.username:
        username_to_id[user.username.lower()] = user.id

    if user.id not in players:
        code = str(random.randint(100000, 999999))
        while code in ref_codes:
            code = str(random.randint(100000, 999999))

        players[user.id] = {
            "name": user.first_name,
            "username": user.username,
            "foot": 0,
            "ref": code,
        }
        ref_codes[code] = user.id
    else:
        # Обновляем имя и юзернейм на случай, если они изменились
        players[user.id]["name"] = user.first_name
        if user.username:
            players[user.id]["username"] = user.username
            username_to_id[user.username.lower()] = user.id

    return players[user.id]


@bot.message_handler(commands=["start"])
def start(message):
    user = message.from_user
    p = get_player(user)

    # Обработка реферальной ссылки (/start 123456)
    command_args = message.text.split()
    if len(command_args) > 1:
        ref_code = command_args[1]
        if ref_code in ref_codes:
            referrer_id = ref_codes[ref_code]
            # Убедимся, что игрок не реферит сам себя и уже записан
            if referrer_id != user.id and referrer_id in players:
                # Проверяем, не использовал ли он уже рефералку (можно добавить флаг, но тут просто бонус)
                players[referrer_id]["foot"] += 10
                bot.send_message(
                    referrer_id,
                    f"🎉 По вашей реферальной ссылке зарегистрировался **{user.first_name}**!\n🦶 Ваша пятка выросла на **10%**!",
                    parse_mode="Markdown",
                )

    bot.reply_to(
        message,
        f"""👋 Привет, {user.first_name}!

🌱 Выращивай пятку и соревнуйся с друзьями!

Команды:
/grow — вырастить пятку (+5%)
/foot — узнать размер своей пятки
/kiss @username — поцеловать пятку
/slap @username — шлёпнуть пятку
/steal @username — украсть проценты пятки
/ref — твоя реферальная ссылка (+10% за друга)
/top — таблица лидеров""",
    )


@bot.message_handler(commands=["grow"])
def grow(message):
    p = get_player(message.from_user)
    p["foot"] += 5
    bot.reply_to(message, f"🌱 Ты вырастил пятку!\nТеперь она {p['foot']}% 🦶")


@bot.message_handler(commands=["foot"])
def foot(message):
    p = get_player(message.from_user)
    bot.reply_to(message, f"👣 Размер твоей пятки: {p['foot']}%")


@bot.message_handler(commands=["kiss"])
def kiss(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "Использование: /kiss @username")
        return

    target_username = args[1].replace("@", "").lower()
    if target_username not in username_to_id:
        bot.reply_to(
            message,
            "❌ Этот пользователь еще не заходил в бота или у него нет юзернейма.",
        )
        return

    target_id = username_to_id[target_username]
    target_player = players.get(target_id)

    bot.reply_to(
        message,
        f"💋 {message.from_user.first_name} нежно поцеловал пятку пользователя @{target_username} ({target_player['name']}) ❤️",
    )


@bot.message_handler(commands=["slap"])
def slap(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "Использование: /slap @username")
        return

    target_username = args[1].replace("@", "").lower()
    if target_username not in username_to_id:
        bot.reply_to(
            message,
            "❌ Этот пользователь еще не заходил в бота или у него нет юзернейма.",
        )
        return

    target_id = username_to_id[target_username]
    target_player = players.get(target_id)

    bot.reply_to(
        message,
        f"🦶 {message.from_user.first_name} смачно шлёпнул пятку @{target_username} ({target_player['name']}) 😂",
    )


@bot.message_handler(commands=["steal"])
def steal(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "Использование: /steal @username")
        return

    target_username = args[1].replace("@", "").lower()
    if target_username not in username_to_id:
        bot.reply_to(
            message, "❌ Жертва не найдена в базе бота (нужно знать @username)."
        )
        return

    target_id = username_to_id[target_username]
    if target_id == message.from_user.id:
        bot.reply_to(message, "🤔 Сам у себя воровать пятку бессмысленно!")
        return

    p = get_player(message.from_user)
    target_p = players[target_id]

    if target_p["foot"] < 3:
        bot.reply_to(
            message,
            f"❌ У @{target_username} слишком маленькая пятка, нечего воровать!",
        )
        return

    value = random.randint(1, 3)
    # Забираем у жертвы, добавляем грабителю
    target_p["foot"] -= value
    p["foot"] += value

    bot.reply_to(
        message,
        f"🕵️ Ты успешно украл {value}% пятки у @{target_username}!\n"
        f"📉 У него осталось: {target_p['foot']}%\n"
        f"📈 Теперь у тебя: {p['foot']}%",
    )


@bot.message_handler(commands=["ref"])
def ref(message):
    p = get_player(message.from_user)
    bot_info = bot.get_me()
    bot.reply_to(
        message,
        f"🎁 Твоя реферальная ссылка:\nhttps://t.me/{bot_info.username}?start={p['ref']}\n\n"
        f"Приглашай друзей и получай **+10%** к пятке за каждого!",
    )


@bot.message_handler(commands=["top"])
def top(message):
    if not players:
        bot.reply_to(message, "Пока никто не играл.")
        return

    rating = sorted(players.values(), key=lambda x: x["foot"], reverse=True)

    text = "🏆 ТОП ПЯТОК\n\n"
    for i, player in enumerate(rating[:10], 1):
        medal = (
            "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        )
        text += f"{medal} {player['name']} — {player['foot']}%\n"

    bot.reply_to(message, text)


print("Бот успешно запущен и ждет команды...")
bot.infinity_polling()
