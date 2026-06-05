def get_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💪 Тренировка", "⚔️ Арена", "🏆 Топ")
    markup.row("🐾 Статус", "🏪 Магазин", "⚡ Прокачка") # Добавлена кнопка
    return markup

@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    user_id = message.from_user.id
    
    # ... (предыдущий код)

    elif message.text == "⚡ Прокачка":
        # Получаем данные игрока
        user_data = supabase.table("pets").select("str, gold").eq("user_id", user_id).execute().data[0]
        
        if user_data['gold'] >= 50:
            # Увеличиваем силу на 5 и отнимаем 50 золота
            new_str = user_data['str'] + 5
            new_gold = user_data['gold'] - 50
            
            supabase.table("pets").update({
                "str": new_str, 
                "gold": new_gold
            }).eq("user_id", user_id).execute()
            
            bot.reply_to(message, f"⚡ Успешно! Твоя сила теперь: {new_str}. Потрачено 50 золота.")
        else:
            bot.reply_to(message, "❌ Недостаточно золота для прокачки (нужно 50).")
