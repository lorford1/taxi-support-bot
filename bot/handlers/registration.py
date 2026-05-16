from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from storage.user_storage import user_storage

router = Router()

# Состояния для регистрации
class RegistrationStates(StatesGroup):
    waiting_for_id = State()
    waiting_for_fullname = State()


# Клавиатура после регистрации
def get_registered_keyboard():
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


def get_unregistered_keyboard():
    buttons = [
        [KeyboardButton(text="📝 Зарегистрироваться")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    telegram_id = str(message.from_user.id)
    
    # Проверяем в постоянном хранилище
    user = user_storage.get_user(telegram_id)
    
    if user:
        # Уже зарегистрирован
        await message.answer(
            f"🚕 <b>С возвращением, {user.get('fullname')}!</b>\n\n"
            f"🆔 Ваш ID: <code>{user.get('driver_id')}</code>\n\n"
            f"Выберите категорию проблемы на кнопках ниже.",
            parse_mode="HTML",
            reply_markup=get_registered_keyboard()
        )
        # Сохраняем в FSM для текущей сессии
        await state.update_data(
            driver_id=user.get('driver_id'),
            fullname=user.get('fullname'),
            registered=True
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
        await state.clear()


@router.message(F.text == "📝 Зарегистрироваться")
async def start_registration(message: Message, state: FSMContext):
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
    driver_id = message.text.strip()
    
    if not driver_id.isdigit():
        await message.answer(
            "❌ <b>Неверный формат ID</b>\n\n"
            "ID должен состоять только из цифр.\n"
            "Пожалуйста, введите ID еще раз:",
            parse_mode="HTML"
        )
        return
    
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
    fullname = message.text.strip()
    
    if len(fullname.split()) < 2:
        await message.answer(
            "❌ <b>Неверный формат ФИО</b>\n\n"
            "Пожалуйста, введите полное ФИО (Фамилия Имя Отчество).\n"
            "Пример: <code>Иванов Иван Иванович</code>",
            parse_mode="HTML"
        )
        return
    
    user_data = await state.get_data()
    driver_id = user_data.get("driver_id")
    telegram_id = str(message.from_user.id)
    
    # Сохраняем в постоянное хранилище
    user_storage.save_user(telegram_id, {
        "driver_id": driver_id,
        "fullname": fullname,
        "telegram_id": telegram_id,
        "telegram_name": message.from_user.full_name,
        "registered_at": message.date.isoformat()
    })
    
    # Сохраняем в FSM
    await state.update_data(
        driver_id=driver_id,
        fullname=fullname,
        registered=True
    )
    
    await message.answer(
        "✅ <b>Регистрация успешно завершена!</b>\n\n"
        f"🆔 Ваш ID: <code>{driver_id}</code>\n"
        f"👤 Ваше ФИО: <b>{fullname}</b>\n\n"
        "Теперь все ваши заявки будут автоматически привязываться к вам.\n\n"
        "Выберите категорию проблемы на кнопках ниже.",
        parse_mode="HTML",
        reply_markup=get_registered_keyboard()
    )


@router.message(F.text == "🆔 Мой профиль")
async def show_profile(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    user = user_storage.get_user(telegram_id)
    
    if user:
        await message.answer(
            "📋 <b>Ваш профиль</b>\n\n"
            f"🆔 <b>ID:</b> <code>{user.get('driver_id')}</code>\n"
            f"👤 <b>ФИО:</b> {user.get('fullname')}\n"
            f"📅 <b>Дата регистрации:</b> {user.get('registered_at', 'неизвестно')[:10]}\n\n"
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
    await state.clear()
    await message.answer(
        "❌ Регистрация отменена.\n\n"
        "Вы можете начать заново, нажав на кнопку <b>📝 Зарегистрироваться</b>.",
        parse_mode="HTML",
        reply_markup=get_unregistered_keyboard()
    )