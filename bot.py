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
    Message,
)

# Настройки
TOKEN = "8838249295:AAGR3CgnAti-xZwRzpe0duvhdrSMmfw-HaE"  # Токен вашего основного бота-магазина
ADMIN_ID = 8680515597  # Ваш Telegram ID для получения уведомлений о заказах

# Данные о товарах
PRODUCTS = {
    "item_1": {
        "name": "Эксклюзивная тойота",
        "price": 12,
        "desc": "Навсегда.",
    },
    "item_2": {
        "name": "Ford F650)",
        "price": 21,
        "desc": "Навсегда.",
    },
}

# Состояния для оформления заказа
class OrderState(StatesGroup):
    waiting_for_payment_proof = State()


router = Router()

# Главное меню / Каталог товаров
@router.message(Command("start"))
async def cmd_start(message: Message):
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

    await message.answer(
        "👋 **Добро пожаловать в магазин цифровых товаров!**\n\n"
        "Выберите интересующий вас товар из списка ниже:",
        reply_markup=markup,
        parse_mode="Markdown",
    )

# Обработка выбора товара
@router.callback_query(F.data.startswith("buy_"))
async def process_purchase(callback: CallbackQuery, state: FSMContext):
    item_key = callback.data.split("_")[1]
    product = PRODUCTS.get(item_key)

    if not product:
        await callback.answer("Товар не найден!", show_alert=True)
        return

    # Сохраняем выбранный товар в память сессии
    await state.update_data(item_name=product["name"], item_price=product["price"])
    await state.set_state(OrderState.waiting_for_payment_proof)

    # Реквизиты для оплаты СБП / Карта
    payment_text = (
        f"🛒 Вы выбрали: **{product['name']}**\n"
        f"💰 Стоимость: **{product['price']} руб.**\n\n"
        f"💳 **Способ оплаты (СБП / Перевод на карту):**\n"
        f"• Банк: Сбер / Т-Банк\n"
        f"• Номер карты: `2200 7021 6141 6974`\n"
        f"• Номер телефона (СБП): `+7 (913) 517-65-93` (Получатель: Рамиль М.)\n\n"
        f"⚠️ **Важно:** после оплаты отправьте в этот чат скриншот чека или текстовое подтверждение (например, последние 4 цифры карты или время перевода), чтобы мы могли проверить платеж."
    )

    cancel_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")]
        ]
    )

    await callback.message.edit_text(payment_text, reply_markup=cancel_markup, parse_mode="Markdown")
    await callback.answer()

# Отмена заказа
@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Заказ отменен. Введите /start для возврата в каталог.")
    await callback.answer()

# Получение подтверждения оплаты от пользователя
@router.message(OrderState.waiting_for_payment_proof)
async def receive_payment_proof(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    item_name = data.get("item_name")
    item_price = data.get("item_price")

    # Формируем сообщение для администратора
    admin_text = (
        f"🚨 **Новый заказ!**\n\n"
        f"👤 Покупатель: @{message.from_user.username} (ID: `{message.from_user.id}`)\n"
        f"📦 Товар: {item_name}\n"
        f"💵 Сумма: {item_price} руб.\n\n"
        f"Проверьте поступление средств на карту/СБП!"
    )

    # Пересылаем доказательство оплаты (чек/скриншот/текст) админу
    await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    await message.forward(ADMIN_ID)

    await message.answer(
        "✅ **Спасибо!** Ваш платеж проверяется администратором.\n"
        "Как только оплата поступит, товар будет отправлен вам в этот чат.",
        parse_mode="Markdown",
    )
    await state.clear()

# Запуск бота
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
