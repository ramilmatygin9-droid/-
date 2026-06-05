import os
import asyncio
import logging
import random
import string
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

user_mails = {}

def generate_password(length=12):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def get_main_keyboard():
    kb = [
        [types.KeyboardButton(text="🆕 Создать почту")],
        [types.KeyboardButton(text="📥 Проверить входящие")],
        [types.KeyboardButton(text="📋 Моя почта")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 **Привет! Я бот-генератор реальных временных почт.**\n\n"
        "Создавай ящики, регистрируйся на сайтах, а коды и письма придут прямо сюда!",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(F.text == "🆕 Создать почту")
async def create_mail(message: types.Message):
    user_id = message.from_user.id
    login = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    domains = ["1secmail.com", "1secmail.org", "1secmail.net"]
    domain = random.choice(domains)
    email = f"{login}@{domain}"
    password = generate_password()
    
    user_mails[user_id] = {
        "email": email, "login": login, "domain": domain, "password": password
    }
    
    text = (
        f"✅ **Ваша новая почта создана!**\n\n"
        f"📧 **Адрес:** `{email}`\n"
        f"🔑 **Пароль:** `{password}`\n\n"
        f"_* Нажми на текст, чтобы скопировать._\n"
        f"Используй её для регистраций, затем жми **'Проверить входящие'**."
    )
    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@dp.message(F.text == "📋 Моя почта")
async def my_mail(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_mails:
        return await message.answer("❌ Сначала нажмите **'Создать почту'**.")
    data = user_mails[user_id]
    await message.answer(f"📋 **Твоя почта:**\n\n📧 Адрес: `{data['email']}`\n🔑 Пароль: `{data['password']}`", parse_mode="Markdown")

@dp.message(F.text == "📥 Проверить входящие")
async def check_inbox(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_mails:
        return await message.answer("❌ Сначала создайте почту!")
    
    data = user_mails[user_id]
    status_msg = await message.answer("🔄 *Проверяю ящик...*", parse_mode="Markdown")
    
    url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={data['login']}&domain={data['domain']}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                messages = await response.json()
                if not messages:
                    await status_msg.edit_text("📭 **Писем пока нет.** Направьте письмо и повторите попытку.", parse_mode="Markdown")
                    return
                await status_msg.delete()
                
                for msg in messages[:3]:
                    msg_id = msg.get("id")
                    detail_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={data['login']}&domain={data['domain']}&id={msg_id}"
                    async with session.get(detail_url) as detail_resp:
                        full_msg = await detail_resp.json()
                        mail_text = (
                            f"📩 **Новое письмо!**\n"
                            f"👤 **От:** {full_msg.get('from')}\n"
                            f"📝 **Тема:** {full_msg.get('subject')}\n"
                            f"───────────────────\n"
                            f"📖 **Текст:**\n{full_msg.get('textBody')}"
                        )
                        await message.answer(mail_text[:4000], parse_mode="Markdown")
        except Exception:
            await status_msg.edit_text("❌ Ошибка соединения с сервером почты.")

async def main():
    await bot.set_my_commands([BotCommand(command="/start", description="Запуск")], scope=BotCommandScopeDefault())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
