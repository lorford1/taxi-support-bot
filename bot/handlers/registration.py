import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from storage.user_storage import user_storage

logger = logging.getLogger(__name__)
router = Router()


class RegistrationStates(StatesGroup):
    waiting_for_id = State()
    waiting_for_fullname = State()


def get_registered_keyboard():
    buttons = [
        [KeyboardButton(text="⛽ Топливная карта")],
        [KeyboardButton(text="💵 Выплаты и зарплата")],
        [KeyboardButton(text="🔐 Доступ к сайту")],
        [KeyboardButton(text="🔧 Техподдержка")],
        [KeyboardButton(text="🆔 Мой профиль")],
        [KeyboardButton(text="🆘 Оператор срочно")],
        [KeyboardButton(text="📞 Оператор")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_unregistered_keyboard():
    buttons = [[KeyboardButton(text="📝 Зарегистрироваться")]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    user = user_storage.get_user(telegram_id)
    
    if user:
        await message.answer(
            f"🚕 <b>С возвращением, {user.get('fullname')}!</b>\n\n"
            f"🆔 Ваш ID: <code>{user.get('driver_id')}</code>",
            parse_mode="HTML",
            reply_markup=get_registered_keyboard()
        )
        await state.update_data(
            driver_id=user.get('driver_id'),
            fullname=user.get('fullname'),
            registered=True
        )
    else:
        await message.answer(
            "🚕 <b>Добро пожаловать!</b>\n\n"
            "🔐 <b>Для начала работы необходимо зарегистрироваться.</b>\n\n"
            "Нажмите <b>📝 Зарегистрироваться</b> или /reg",
            parse_mode="HTML",
            reply_markup=get_unregistered_keyboard()
        )
        await state.clear()


@router.message(Command("reg"))
async def reg_command(message: Message, state: FSMContext):
    logger.info(f"🔍 Команда /reg от {message.from_user.id}")
    await message.answer(
        "📝 <b>Регистрация водителя</b>\n\n"
        "Введите ваш <b>ID</b> (только цифры):\n\n"
        "Пример: <code>28282</code>\n\n"
        "Для отмены: /cancel",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(RegistrationStates.waiting_for_id)


@router.message(F.text == "📝 Зарегистрироваться")
async def start_registration(message: Message, state: FSMContext):
    logger.info(f"🔍 Кнопка регистрации от {message.from_user.id}")
    await message.answer(
        "📝 <b>Регистрация водителя</b>\n\n"
        "Введите ваш <b>ID</b> (только цифры):\n\n"
        "Пример: <code>28282</code>\n\n"
        "Для отмены: /cancel",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(RegistrationStates.waiting_for_id)


@router.message(RegistrationStates.waiting_for_id)
async def process_id(message: Message, state: FSMContext):
    logger.info(f"🔍 PROCESS_ID: получил '{message.text}' от {message.from_user.id}")
    
    driver_id = message.text.strip()
    
    if not driver_id.isdigit():
        await message.answer(
            "❌ <b>Неверный формат ID</b>\n\n"
            "ID должен состоять только из цифр.\n"
            "Попробуйте еще раз:",
            parse_mode="HTML"
        )
        return
    
    await state.update_data(driver_id=driver_id)
    logger.info(f"✅ ID сохранён: {driver_id}")
    
    await message.answer(
        "✅ <b>ID принят!</b>\n\n"
        "Теперь введите ваше <b>полное ФИО</b>:\n\n"
        "Пример: <code>Иванов Иван Иванович</code>",
        parse_mode="HTML"
    )
    await state.set_state(RegistrationStates.waiting_for_fullname)


@router.message(RegistrationStates.waiting_for_fullname)
async def process_fullname(message: Message, state: FSMContext):
    logger.info(f"🔍 PROCESS_FULLNAME: получил '{message.text}' от {message.from_user.id}")
    
    fullname = message.text.strip()
    
    if len(fullname.split()) < 2:
        await message.answer(
            "❌ <b>Неверный формат ФИО</b>\n\n"
            "Введите полное ФИО (Фамилия Имя Отчество):",
            parse_mode="HTML"
        )
        return
    
    user_data = await state.get_data()
    driver_id = user_data.get("driver_id")
    telegram_id = str(message.from_user.id)
    
    user_storage.save_user(telegram_id, {
        "driver_id": driver_id,
        "fullname": fullname,
        "telegram_id": telegram_id,
        "telegram_name": message.from_user.full_name,
        "registered_at": message.date.isoformat()
    })
    
    await state.update_data(
        driver_id=driver_id,
        fullname=fullname,
        registered=True
    )
    
    logger.info(f"✅ Регистрация завершена: {fullname} (ID: {driver_id})")
    
    await message.answer(
        f"✅ <b>Регистрация успешно завершена!</b>\n\n"
        f"🆔 <b>ID:</b> <code>{driver_id}</code>\n"
        f"👤 <b>ФИО:</b> {fullname}\n\n"
        f"Теперь выберите категорию проблемы:",
        parse_mode="HTML",
        reply_markup=get_registered_keyboard()
    )


@router.message(Command("cancel"))
async def cancel_registration(message: Message, state: FSMContext):
    current_state = await state.get_state()
    logger.info(f"🔍 Cancel в состоянии: {current_state}")
    
    if current_state in [RegistrationStates.waiting_for_id, RegistrationStates.waiting_for_fullname]:
        await message.answer(
            "❌ Регистрация отменена.\n\n"
            "Нажмите '📝 Зарегистрироваться' для новой попытки.",
            reply_markup=get_unregistered_keyboard()
        )
        await state.clear()
    else:
        await message.answer(
            "❌ Нет активной регистрации.",
            reply_markup=get_unregistered_keyboard()
        )


@router.message(F.text == "🆔 Мой профиль")
async def show_profile(message: Message):
    telegram_id = str(message.from_user.id)
    user = user_storage.get_user(telegram_id)
    
    if user:
        await message.answer(
            f"📋 <b>Ваш профиль</b>\n\n"
            f"🆔 ID: <code>{user.get('driver_id')}</code>\n"
            f"👤 ФИО: {user.get('fullname')}\n"
            f"📅 Зарегистрирован: {user.get('registered_at', 'неизвестно')[:10]}",
            parse_mode="HTML",
            reply_markup=get_registered_keyboard()
        )
    else:
        await message.answer(
            "❌ Вы не зарегистрированы.\n\nНажмите '📝 Зарегистрироваться'.",
            reply_markup=get_unregistered_keyboard()
        )