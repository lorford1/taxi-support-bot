from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from core.planfix_client import planfix

router = Router()

# Состояния для регистрации
class RegistrationStates(StatesGroup):
    waiting_for_id = State()
    waiting_for_fullname = State()


# Клавиатура после регистрации
def get_registered_keyboard():
    """Клавиатура для зарегистрированного пользователя"""
    buttons = [
        [KeyboardButton(text="⛽ Топливная карта")],
        [KeyboardButton(text="💵 Выплаты и зарплата")],
        [KeyboardButton(text="🔐 Доступ к сайту")],
        [KeyboardButton(text="🔧 Техподдержка")],
        [KeyboardButton(text="🆔 Мой профиль")],
        [KeyboardButton(text="📞 Оператор")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# Клавиатура для незарегистрированного пользователя
def get_unregistered_keyboard():
    """Клавиатура для незарегистрированного пользователя"""
    buttons = [
        [KeyboardButton(text="📝 Зарегистрироваться")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    # Проверяем, зарегистрирован ли пользователь
    user_data = await state.get_data()
    
    if user_data.get("registered"):
        # Уже зарегистрирован
        await message.answer(
            f"🚕 <b>С возвращением, {user_data.get('fullname')}!</b>\n\n"
            f"🆔 Ваш ID: {user_data.get('driver_id')}\n\n"
            f"Выберите категорию проблемы на кнопках ниже.",
            parse_mode="HTML",
            reply_markup=get_registered_keyboard()
        )
    else:
        # Не зарегистрирован
        await message.answer(
            "🚕 <b>Добро пожаловать в службу поддержки такси!</b>\n\n"
            "🔐 <b>Для начала работы необходимо зарегистрироваться.</b>\n\n"
            "Нажмите на кнопку <b>📝 Зарегистрироваться</b> и укажите ваш ID и ФИО.\n\n"
            "Это поможет быстрее обрабатывать ваши заявки.",
            parse_mode="HTML",
            reply_markup=get_unregistered_keyboard()
        )


@router.message(F.text == "📝 Зарегистрироваться")
async def start_registration(message: Message, state: FSMContext):
    """Начало процесса регистрации"""
    await message.answer(
        "📝 <b>Регистрация водителя</b>\n\n"
        "Пожалуйста, введите ваш <b>ID</b> (номер водителя в системе).\n\n"
        "Пример: <code>28282</code>\n\n"
        "Для отмены регистрации напишите /cancel",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(RegistrationStates.waiting_for_id)


@router.message(RegistrationStates.waiting_for_id)
async def process_id(message: Message, state: FSMContext):
    """Обработка ID водителя"""
    driver_id = message.text.strip()
    
    # Проверяем, что ID состоит из цифр
    if not driver_id.isdigit():
        await message.answer(
            "❌ <b>Неверный формат ID</b>\n\n"
            "ID должен состоять только из цифр.\n"
            "Пожалуйста, введите ID еще раз:",
            parse_mode="HTML"
        )
        return
    
    # Сохраняем ID
    await state.update_data(driver_id=driver_id)
    
    await message.answer(
        "✅ ID принят!\n\n"
        "Теперь введите ваше <b>полное ФИО</b>.\n\n"
        "Пример: <code>Иванов Иван Иванович</code>",
        parse_mode="HTML"
    )
    await state.set_state(RegistrationStates.waiting_for_fullname)


@router.message(RegistrationStates.waiting_for_fullname)
async def process_fullname(message: Message, state: FSMContext):
    """Обработка ФИО водителя"""
    fullname = message.text.strip()
    
    # Простая проверка: должно быть минимум 2 слова
    if len(fullname.split()) < 2:
        await message.answer(
            "❌ <b>Неверный формат ФИО</b>\n\n"
            "Пожалуйста, введите полное ФИО (Фамилия Имя Отчество).\n"
            "Пример: <code>Иванов Иван Иванович</code>",
            parse_mode="HTML"
        )
        return
    
    # Получаем сохранённый ID
    user_data = await state.get_data()
    driver_id = user_data.get("driver_id")
    
    # Сохраняем данные
    await state.update_data(
        fullname=fullname,
        registered=True
    )
    
    # Можно также проверить водителя в Planfix (опционально)
    # contact = await planfix.find_contact_by_name(fullname)
    
    await message.answer(
        "✅ <b>Регистрация успешно завершена!</b>\n\n"
        f"🆔 Ваш ID: <code>{driver_id}</code>\n"
        f"👤 Ваше ФИО: <b>{fullname}</b>\n\n"
        "Теперь все ваши заявки будут автоматически привязываться к вам.\n\n"
        "Выберите категорию проблемы на кнопках ниже.",
        parse_mode="HTML",
        reply_markup=get_registered_keyboard()
    )
    
    await state.clear()


@router.message(F.text == "🆔 Мой профиль")
async def show_profile(message: Message, state: FSMContext):
    """Показать профиль водителя"""
    user_data = await state.get_data()
    
    if user_data.get("registered"):
        await message.answer(
            "📋 <b>Ваш профиль</b>\n\n"
            f"🆔 <b>ID:</b> <code>{user_data.get('driver_id')}</code>\n"
            f"👤 <b>ФИО:</b> {user_data.get('fullname')}\n"
            f"📅 <b>Дата регистрации:</b> {message.date.strftime('%d.%m.%Y')}\n\n"
            "Если данные неверны, обратитесь к оператору.",
            parse_mode="HTML",
            reply_markup=get_registered_keyboard()
        )
    else:
        await message.answer(
            "❌ Вы не зарегистрированы.\n\n"
            "Нажмите на кнопку <b>📝 Зарегистрироваться</b>.",
            parse_mode="HTML",
            reply_markup=get_unregistered_keyboard()
        )


@router.message(Command("cancel"))
async def cancel_registration(message: Message, state: FSMContext):
    """Отмена регистрации"""
    await state.clear()
    await message.answer(
        "❌ Регистрация отменена.\n\n"
        "Вы можете начать заново, нажав на кнопку <b>📝 Зарегистрироваться</b>.",
        parse_mode="HTML",
        reply_markup=get_unregistered_keyboard()
    )


# Обновляем обработчик проблем, чтобы использовать данные водителя
@router.message(F.text == "⛽ Топливная карта")
async def fuel_card_category(message: Message, state: FSMContext):
    """Категория топливной карты с идентификацией"""
    user_data = await state.get_data()
    
    if not user_data.get("registered"):
        await message.answer(
            "❌ Для использования бота необходимо сначала зарегистрироваться.\n\n"
            "Нажмите на кнопку <b>📝 Зарегистрироваться</b>.",
            parse_mode="HTML",
            reply_markup=get_unregistered_keyboard()
        )
        return
    
    await message.answer(
        f"⛽ <b>Выберите проблему с топливной картой</b>\n\n"
        f"👤 Водитель: {user_data.get('fullname')}\n"
        f"🆔 ID: {user_data.get('driver_id')}\n\n"
        "• Разблокировать карту\n"
        "• Обновить лимит\n"
        "• Не работает на заправке\n"
        "• Заказать новую карту",
        parse_mode="HTML"
    )