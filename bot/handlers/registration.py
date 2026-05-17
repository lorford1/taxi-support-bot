import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from storage.user_storage import user_storage
from bot.keyboards.menu import get_registered_keyboard, get_unregistered_keyboard

logger = logging.getLogger(__name__)
router = Router()


class RegistrationStates(StatesGroup):
    waiting_for_id = State()
    waiting_for_fullname = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    telegram_id = str(message.from_user.id)
    user = user_storage.get_user(telegram_id)
    
    if user:
        await message.answer(
            f"🚕 <b>С возвращением, {user.get('fullname')}!</b>\n\n"
            f"🆔 Ваш ID: <code>{user.get('driver_id')}</code>\n\n"
            f"📝 <b>Просто напишите вашу проблему</b> — я проанализирую и создам заявку.\n\n"
            f"Примеры:\n"
            f"• Деньги не пришли на карту\n"
            f"• Карта заблокировалась на заправке\n"
            f"• Не могу зайти в личный кабинет",
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
            "🚕 <b>Добро пожаловать в службу поддержки такси!</b>\n\n"
            "🔐 <b>Для начала работы необходимо зарегистрироваться.</b>\n\n"
            "Нажмите на кнопку <b>📝 Зарегистрироваться</b>",
            parse_mode="HTML",
            reply_markup=get_unregistered_keyboard()
        )
        await state.clear()


@router.message(Command("reg"))
async def reg_command(message: Message, state: FSMContext):
    """Команда /reg - начать регистрацию"""
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
    """Нажатие на кнопку регистрации"""
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
    """Обработка ID водителя"""
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
    """Обработка ФИО водителя и завершение регистрации"""
    logger.info(f"🔍 PROCESS_FULLNAME: получил '{message.text}' от {message.from_user.id}")
    
    fullname = message.text.strip()
    
    # Проверяем, что это не команда или кнопка
    if fullname in ["❓ Помощь", "📞 Оператор"]:
        await message.answer(
            "❌ Пожалуйста, введите ваше ФИО (Фамилия Имя Отчество), а не кнопку меню.",
            parse_mode="HTML"
        )
        return
    
    if len(fullname.split()) < 2:
        await message.answer(
            "❌ <b>Неверный формат ФИО</b>\n\n"
            "Введите полное ФИО (Фамилия Имя Отчество):\n"
            "Пример: <code>Иванов Иван Иванович</code>",
            parse_mode="HTML"
        )
        return
    
    user_data = await state.get_data()
    driver_id = user_data.get("driver_id")
    telegram_id = str(message.from_user.id)
    
    if not driver_id:
        await message.answer(
            "❌ Ошибка: ID не найден. Начните регистрацию заново: /reg",
            reply_markup=get_unregistered_keyboard()
        )
        await state.clear()
        return
    
    # Сохраняем в базу данных
    user_storage.save_user(telegram_id, {
        "driver_id": driver_id,
        "fullname": fullname,
        "telegram_id": telegram_id,
        "telegram_name": message.from_user.full_name,
        "telegram_username": message.from_user.username,
        "registered_at": message.date.isoformat()
    })
    
    await state.update_data(
        driver_id=driver_id,
        fullname=fullname,
        registered=True
    )
    
    # Очищаем состояние
    await state.clear()
    
    logger.info(f"✅ Регистрация завершена: {fullname} (ID: {driver_id})")
    
    await message.answer(
        f"✅ <b>Регистрация успешно завершена!</b>\n\n"
        f"🆔 <b>Ваш ID:</b> <code>{driver_id}</code>\n"
        f"👤 <b>Ваше ФИО:</b> {fullname}\n\n"
        f"📝 <b>Теперь просто напишите вашу проблему</b> — я проанализирую и создам заявку.\n\n"
        f"Примеры:\n"
        f"• Деньги не пришли на карту\n"
        f"• Карта заблокировалась на заправке\n"
        f"• Не могу зайти в личный кабинет",
        parse_mode="HTML",
        reply_markup=get_registered_keyboard()
    )


@router.message(Command("cancel"))
async def cancel_registration(message: Message, state: FSMContext):
    """Отмена регистрации"""
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
            "❌ Нет активной регистрации для отмены.",
            reply_markup=get_unregistered_keyboard()
        )