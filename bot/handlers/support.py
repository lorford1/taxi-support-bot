from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext

from bot.keyboards.menu import (
    get_main_keyboard,
    get_fuel_card_keyboard,
    get_payments_keyboard,
    get_access_keyboard,
    get_support_keyboard
)
from bot.handlers.registration import (
    router as registration_router,
    get_registered_keyboard,
    get_unregistered_keyboard
)
from core.planfix_client import planfix

router = Router()

# Подключаем роутер регистрации
router.include_router(registration_router)

# База ответов (можно расширить)
ANSWERS = {
    "разблокировать карту": "🔓 Хорошо, {name}, я создал заявку на разблокировку вашей топливной карты.\n\nНомер заявки: #{}\n\n⏱️ Обычно занимает до 30 минут.",
    # ... остальные ответы
}


@router.message(F.text == "🔓 Разблокировать карту")
async def unblock_card(message: Message, state: FSMContext):
    """Разблокировка карты с привязкой к водителю"""
    user_data = await state.get_data()
    
    if not user_data.get("registered"):
        await message.answer("❌ Сначала зарегистрируйтесь (кнопка 📝 Зарегистрироваться)")
        return
    
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
    result = await planfix.create_task(
        title=f"⛽ Разблокировка карты: {driver_name} (ID: {driver_id})",
        description=f"""
Запрос на разблокировку топливной карты

👤 Водитель: {driver_name}
🆔 ID: {driver_id}
📅 Время: {message.date}
        """
    )
    
    if result.get("success"):
        await message.answer(
            ANSWERS["разблокировать карту"].format(driver_name, result.get('general')),
            parse_mode=ParseMode.HTML
        )
    else:
        await message.answer("⛽ Создал заявку на разблокировку. Специалист свяжется с вами.")


# Аналогично обновите другие обработчики