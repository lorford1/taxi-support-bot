from storage.user_storage import user_storage


@router.message(F.text == "⛽ Топливная карта")
async def fuel_card_category(message: Message, state: FSMContext):
    """Категория топливной карты с проверкой регистрации"""
    telegram_id = str(message.from_user.id)
    user = user_storage.get_user(telegram_id)
    
    if not user:
        await message.answer(
            "❌ Для использования бота необходимо сначала зарегистрироваться.\n\n"
            "Нажмите на кнопку <b>📝 Зарегистрироваться</b>.",
            parse_mode="HTML",
            reply_markup=get_unregistered_keyboard()
        )
        return
    
    await message.answer(
        f"⛽ <b>Выберите проблему с топливной картой</b>\n\n"
        f"👤 Водитель: {user.get('fullname')}\n"
        f"🆔 ID: {user.get('driver_id')}\n\n"
        "• Разблокировать карту\n"
        "• Обновить лимит\n"
        "• Не работает на заправке\n"
        "• Заказать новую карту",
        parse_mode="HTML"
    )