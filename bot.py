import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Message,
)

# Токен прописан напрямую для стабильного запуска
TOKEN = "8838249295:AAGR3CgnAti-xZwRzpe0duvhdrSMmfw-HaE"
ADMIN_ID = 8680515597

PRODUCTS = {
    "item_1": {
        "name": "🚗 Эксклюзивная тойота",
        "price": 12,
        "desc": "Тюнинг, фулл прокачка. Передача через сделку в игре.",
    },
    "item_2": {
        "name": "🚙 Ford F650",
        "price": 21,
        "desc": "Огромный пикап, эксклюзивный цвет.",
    },
}

class OrderState(StatesGroup):
    waiting_for_payment_proof = State()

router = Router()

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Каталог товаров"), KeyboardButton(text="ℹ️ Информация")],
            [KeyboardButton(text="📞 Поддержка")]
        ],
        resize_keyboard=True
    )

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привет, **{message.from_user.first_name}**!\n\n"
        "Добро пожаловать в магазин аккаунтов и машин **Car Parking Multiplayer**.\n"
        "Выберите нужное действие в меню ниже:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@router.message(F.text == "🛍 Каталог товаров")
async def show_catalog(message: Message):
    keyboard_buttons = []
    for key, product in PRODUCTS.items():
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{product['name']} — {product['price']} руб.",
                    callback_data=f"buy_{key}",
                )
            ]
        )
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.answer("🚗 **Доступные товары для покупки:**", reply_markup=markup, parse_mode="Markdown")

@router.message(F.text == "ℹ️ Информация")
async def show_info(message: Message):
    await message.answer(
        "📌 **Как купить товар?**\n\n"
        "1. Перейдите в «🛍 Каталог товаров».\n"
        "2. Выберите нужную машину.\n"
        "3. Оплатите по реквизитам СБП или карты.\n"
        "4. Отправьте скриншот чека в этот чат.\n"
        "5. Администратор проверит платеж и выдаст товар!",
        parse_mode="Markdown"
    )

@router.message(F.text == "📞 Поддержка")
async def show_support(message: Message):
    await message.answer("💬 Возникли вопросы? Напишите администратору: @Ramil")

@router.callback_query(F.data.startswith("buy_"))
async def process_purchase(callback: CallbackQuery, state: FSMContext):
    item_key = callback.data.split("_")[1]
    product = PRODUCTS.get(item_key)

    if not product:
        await callback.answer("Товар не найден!", show_alert=True)
        return

    await state.update_data(item_name=product["name"], item_price=product["price"])
    await state.set_state(OrderState.waiting_for_payment_proof)

    payment_text = (
        f"🛒 Вы выбрали: **{product['name']}**\n"
        f"📝 Описание: {product['desc']}\n"
        f"💰 Стоимость: **{product['price']} руб.**\n\n"
        f"💳 **Реквизиты для оплаты (СБП / Карта):**\n"
        f"• Банк: Сбер / Т-Банк\n"
        f"• Номер карты: `2200 7021 6141 6974`\n"
        f"• СБП телефон: `+7 (913) 517-65-93` (Рамиль М.)\n\n"
        f"⚠️ **После оплаты отправьте сюда скриншот чека или фото перевода!**"
    )

    cancel_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить заказ", callback_data="cancel_order")]
        ]
    )

    await callback.message.answer(payment_text, reply_markup=cancel_markup, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Заказ отменен.", reply_markup=get_main_keyboard())
    await callback.answer()

@router.message(OrderState.waiting_for_payment_proof)
async def receive_payment_proof(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    item_name = data.get("item_name")
    item_price = data.get("item_price")

    admin_text = (
        f"🚨 **Новый чек по заказу!**\n\n"
        f"👤 Покупатель: @{message.from_user.username} (ID: `{message.from_user.id}`)\n"
        f"📦 Товар: {item_name}\n"
        f"💵 Сумма: {item_price} руб."
    )

    await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    await message.forward(ADMIN_ID)

    await message.answer(
        "✅ **Чек отправлен администратору!**\nОжидайте проверки, скоро с вами свяжутся.",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
    await state.clear()

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
