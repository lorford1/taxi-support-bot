import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import aiohttp

from bot.keyboards.menu import (
    get_main_keyboard,
    get_fuel_card_keyboard,
    get_payments_keyboard,
    get_access_keyboard,
    get_support_keyboard
)
from storage.user_storage import user_storage
from core.llm_intent import llm_classifier

logger = logging.getLogger(__name__)
router = Router()

# URL вебхука Planfix
WEBHOOK_URL = "https://taxit.planfix.ru/webhook/get/j0tc-k18j-5jf6-bqvh"
PROJECT_ID = None


# ============ СОСТОЯНИЯ ДЛЯ СРОЧНОГО ОПЕРАТОРА ============
class UrgentOperatorStates(StatesGroup):
    waiting_for_message = State()


# ============ КЛАВИАТУРЫ ============

def get_registered_keyboard():
    from bot.handlers.registration import get_registered_keyboard as grk
    return grk()


def get_unregistered_keyboard():
    from bot.handlers.registration import get_unregistered_keyboard as guk
    return guk()


async def create_task_via_webhook(title: str, description: str) -> bool:
    """Создание задачи через входящий вебхук Planfix"""
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    params = {
        "name": title,
        "description": description,
        "startDate": today,
        "endDate": tomorrow
    }
    
    if PROJECT_ID:
        params["project"] = PROJECT_ID
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(WEBHOOK_URL, params=params) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Ошибка вебхука: {e}")
        return False


async def check_registration(message: Message, state: FSMContext):
    """Проверка регистрации через БД"""
    telegram_id = str(message.from_user.id)
    user = user_storage.get_user(telegram_id)
    
    if not user:
        await message.answer(
            "❌ Сначала зарегистрируйтесь (/reg)",
            reply_markup=get_unregistered_keyboard()
        )
        return None
    
    # Обновляем state
    await state.update_data(
        driver_id=user.get('driver_id'),
        fullname=user.get('fullname'),
        registered=True
    )
    return user


# ============ ОБРАБОТЧИК СРОЧНОГО ОПЕРАТОРА ============

@router.message(F.text == "🆘 Оператор срочно")
async def urgent_operator_start(message: Message, state: FSMContext):
    """Начало срочного вызова оператора — запрос сообщения"""
    user = await check_registration(message, state)
    if not user:
        return
    
    driver_name = user.get('fullname', message.from_user.full_name)
    
    await message.answer(
        f"🚨 <b>Срочный вызов оператора, {driver_name}!</b>\n\n"
        f"Пожалуйста, напишите одним сообщением:\n"
        f"• Вашу проблему\n"
        f"• Что случилось\n"
        f"• Что нужно сделать\n\n"
        f"📌 Для отмены напишите /cancel",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(UrgentOperatorStates.waiting_for_message)


@router.message(UrgentOperatorStates.waiting_for_message)
async def urgent_operator_process(message: Message, state: FSMContext):
    """Получение сообщения от водителя и создание срочной задачи"""
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', message.from_user.full_name)
    driver_id = user_data.get('driver_id', 'не указан')
    
    user_message = message.text.strip()
    
    if len(user_message) < 5:
        await message.answer(
            "❌ Пожалуйста, напишите более подробное сообщение (минимум 5 символов).",
            parse_mode="HTML"
        )
        return
    
    status_msg = await message.answer("🚨 Отправляю срочный запрос оператору...")
    
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    title = f"🚨 СРОЧНЫЙ ВЫЗОВ ОПЕРАТОРА: {driver_name} (ID: {driver_id})"
    description = f"""
🚨 СРОЧНОЕ ОБРАЩЕНИЕ ВОДИТЕЛЯ

👤 Водитель: {driver_name}
🆔 ID: {driver_id}
📅 Время: {today}
📱 Telegram ID: {message.from_user.id}

📝 СООБЩЕНИЕ ВОДИТЕЛЯ:
{user_message}

⚠️ ТРЕБУЕТСЯ СРОЧНОЕ ВМЕШАТЕЛЬСТВО!
    """
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            f"🚨 <b>Срочный запрос отправлен, {driver_name}!</b>\n\n"
            f"✅ Ваше сообщение передано оператору\n"
            f"👨‍💼 Оператор свяжется с вами в ближайшее время!",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            f"❌ <b>Ошибка при отправке срочного запроса!</b>\n\n"
            f"Пожалуйста, напишите '📞 Оператор'.",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
    
    await state.clear()


# ============ ОСНОВНЫЕ КОМАНДЫ ============

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    user = user_storage.get_user(telegram_id)
    
    if user:
        await message.answer(
            f"🚕 <b>С возвращением, {user.get('fullname')}!</b>\n\n"
            f"🆔 Ваш ID: <code>{user.get('driver_id')}</code>\n\n"
            f"Выберите категорию проблемы:",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
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
            "Нажмите на кнопку <b>📝 Зарегистрироваться</b> или напишите /reg",
            parse_mode="HTML",
            reply_markup=get_unregistered_keyboard()
        )
        await state.clear()


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 <b>Как пользоваться ботом:</b>\n\n"
        "1️⃣ Нажмите на категорию проблемы\n"
        "2️⃣ Выберите конкретную проблему\n\n"
        "<b>Или просто напишите проблему словами!</b>\n\n"
        "<b>Срочный вызов оператора:</b>\n"
        "🆘 Нажмите 'Оператор срочно'\n\n"
        "<b>Команды:</b>\n"
        "/start — главное меню\n"
        "/help — эта справка\n"
        "/reg — зарегистрироваться\n"
        "/cancel — отмена",
        parse_mode="HTML"
    )


@router.message(Command("cancel"))
async def cancel_action(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    current_state = await state.get_state()
    
    if current_state == UrgentOperatorStates.waiting_for_message:
        await message.answer(
            "❌ Срочный вызов отменён.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
    else:
        await message.answer(
            "❌ Нет активных действий для отмены.",
            reply_markup=get_main_keyboard()
        )


# ============ НАВИГАЦИЯ ============

@router.message(F.text == "◀️ Назад")
async def back_to_main(message: Message):
    await message.answer(
        "🏠 <b>Главное меню</b>",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "❓ Помощь")
async def help_button(message: Message):
    await cmd_help(message)


@router.message(F.text == "📞 Оператор")
async def call_operator(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    driver_name = user.get('fullname', message.from_user.full_name)
    driver_id = user.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Создаю заявку...")
    
    title = f"📞 Вызов оператора: {driver_name} (ID: {driver_id})"
    description = f"""
👤 Водитель: {driver_name}
🆔 ID: {driver_id}
📅 Время: {message.date}
    """
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            f"👨‍💼 <b>Заявка создана!</b>\n\nСпециалист свяжется с вами.",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"❌ Ошибка. Нажмите '🆘 Оператор срочно'.",
            parse_mode="HTML"
        )


# ============ КАТЕГОРИЯ: ТОПЛИВНАЯ КАРТА ============

@router.message(F.text == "⛽ Топливная карта")
async def fuel_card_category(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    await message.answer(
        f"⛽ <b>Выберите проблему:</b>\n\n"
        f"👤 {user.get('fullname')}\n\n"
        "• 🔓 Разблокировать карту\n"
        "• 📈 Обновить лимит\n"
        "• ⛽ Не работает на заправке\n"
        "• 🆕 Заказать новую карту",
        parse_mode="HTML",
        reply_markup=get_fuel_card_keyboard()
    )


@router.message(F.text == "🔓 Разблокировать карту")
async def unblock_card(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    driver_name = user.get('fullname', 'водитель')
    driver_id = user.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Отправляю запрос...")
    
    title = f"⛽ Разблокировка карты: {driver_name} (ID: {driver_id})"
    description = f"Водитель: {driver_name}\nID: {driver_id}"
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            f"🔓 <b>Хорошо, {driver_name}!</b>\n\n✅ Заявка создана!",
            parse_mode="HTML",
            reply_markup=get_fuel_card_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка. Нажмите '🆘 Оператор срочно'.",
            reply_markup=get_fuel_card_keyboard()
        )


@router.message(F.text == "📈 Обновить лимит")
async def update_limit(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    driver_name = user.get('fullname', 'водитель')
    driver_id = user.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Отправляю запрос...")
    
    title = f"📈 Обновление лимита: {driver_name} (ID: {driver_id})"
    description = f"Запрос на обновление лимита"
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            f"📈 <b>Заявка создана!</b>\n\nЛимит будет обновлён.",
            parse_mode="HTML",
            reply_markup=get_fuel_card_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка. Нажмите '🆘 Оператор срочно'.",
            reply_markup=get_fuel_card_keyboard()
        )


@router.message(F.text == "⛽ Не работает на заправке")
async def card_not_working(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    driver_name = user.get('fullname', 'водитель')
    driver_id = user.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Отправляю запрос...")
    
    title = f"⛽ Проблема на заправке: {driver_name} (ID: {driver_id})"
    description = f"Карта не работает на заправке"
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            f"⛽ <b>Заявка создана!</b>\n\nСпециалист проверит.",
            parse_mode="HTML",
            reply_markup=get_fuel_card_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка. Нажмите '🆘 Оператор срочно'.",
            reply_markup=get_fuel_card_keyboard()
        )


@router.message(F.text == "🆕 Заказать новую карту")
async def order_new_card(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    driver_name = user.get('fullname', 'водитель')
    
    await message.answer(
        f"🆕 <b>{driver_name}, заказать новую карту</b>\n\n"
        f"🔗 Ссылка: <code>https://proracers.by/bncard</code>\n\n"
        f"💡 Если не пришло SMS — нажмите '🆘 Оператор срочно'.",
        parse_mode="HTML",
        reply_markup=get_fuel_card_keyboard(),
        disable_web_page_preview=True
    )


# ============ КАТЕГОРИЯ: ВЫПЛАТЫ ============

@router.message(F.text == "💵 Выплаты и зарплата")
async def payments_category(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    await message.answer(
        "💵 <b>Выберите проблему:</b>\n\n"
        "• 💰 Вывести деньги на карту\n"
        "• ❓ Где мои деньги?\n"
        "• 📈 Увеличить квоту\n"
        "• 💳 Ошибка в реквизитах",
        parse_mode="HTML",
        reply_markup=get_payments_keyboard()
    )


@router.message(F.text == "💰 Вывести деньги на карту")
async def withdraw_money(message: Message):
    await message.answer(
        "💰 <b>Инструкция:</b>\n\n"
        "1️⃣ proracers.by/exchange\n"
        "2️⃣ Укажите IBAN\n"
        "3️⃣ Укажите ФИО",
        parse_mode="HTML",
        reply_markup=get_payments_keyboard(),
        disable_web_page_preview=True
    )


@router.message(F.text == "❓ Где мои деньги?")
async def where_is_money(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    driver_name = user.get('fullname', 'водитель')
    driver_id = user.get('driver_id', 'не указан')
    
    title = f"💰 Проверка выплаты: {driver_name} (ID: {driver_id})"
    success = await create_task_via_webhook(title, "Запрос на проверку выплаты")
    
    if success:
        await message.answer(
            "🔍 <b>Заявка создана!</b>\n\nДеньги обычно поступают в течение рабочего дня.",
            parse_mode="HTML",
            reply_markup=get_payments_keyboard()
        )
    else:
        await message.answer("❌ Ошибка. Нажмите '🆘 Оператор срочно'.", reply_markup=get_payments_keyboard())


@router.message(F.text == "📈 Увеличить квоту")
async def increase_quota(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    driver_name = user.get('fullname', 'водитель')
    driver_id = user.get('driver_id', 'не указан')
    
    title = f"📈 Увеличение квоты: {driver_name} (ID: {driver_id})"
    success = await create_task_via_webhook(title, "Запрос на увеличение квоты")
    
    if success:
        await message.answer(
            "📈 <b>Заявка создана!</b>\n\nМенеджер свяжется с вами.",
            parse_mode="HTML",
            reply_markup=get_payments_keyboard()
        )
    else:
        await message.answer("❌ Ошибка.", reply_markup=get_payments_keyboard())


@router.message(F.text == "💳 Ошибка в реквизитах")
async def wrong_details(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    driver_name = user.get('fullname', 'водитель')
    driver_id = user.get('driver_id', 'не указан')
    
    title = f"💳 Ошибка в реквизитах: {driver_name} (ID: {driver_id})"
    success = await create_task_via_webhook(title, "Запрос на проверку реквизитов")
    
    if success:
        await message.answer(
            "💳 <b>Заявка создана!</b>\n\nПроверьте правильность IBAN и ФИО.",
            parse_mode="HTML",
            reply_markup=get_payments_keyboard()
        )
    else:
        await message.answer("❌ Ошибка.", reply_markup=get_payments_keyboard())


# ============ КАТЕГОРИЯ: ДОСТУП К САЙТУ ============

@router.message(F.text == "🔐 Доступ к сайту")
async def access_category(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    await message.answer(
        "🔐 <b>Выберите проблему:</b>\n\n"
        "• 🔓 Открыть доступ\n"
        "• 📝 Зарегистрироваться на сайте\n"
        "• 🔄 Восстановить пароль",
        parse_mode="HTML",
        reply_markup=get_access_keyboard()
    )


@router.message(F.text == "🔓 Открыть доступ")
async def open_access(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    driver_name = user.get('fullname', 'водитель')
    driver_id = user.get('driver_id', 'не указан')
    
    title = f"🔐 Запрос доступа: {driver_name} (ID: {driver_id})"
    success = await create_task_via_webhook(title, "Запрос на открытие доступа")
    
    if success:
        await message.answer(
            "🔐 <b>Доступ предоставлен!</b>\n\nВойдите на сайт: proracers.by",
            parse_mode="HTML",
            reply_markup=get_access_keyboard(),
            disable_web_page_preview=True
        )
    else:
        await message.answer("❌ Ошибка.", reply_markup=get_access_keyboard())


@router.message(F.text == "📝 Зарегистрироваться на сайте")
async def register_site(message: Message):
    await message.answer(
        "📝 <b>Регистрация на сайте</b>\n\n"
        "1️⃣ proracers.by\n"
        "2️⃣ Нажмите 'Регистрация'\n"
        "3️⃣ Укажите почту (Gmail)\n"
        "4️⃣ Заполните ФИО и ID\n\n"
        "✅ После регистрации напишите сюда.",
        parse_mode="HTML",
        reply_markup=get_access_keyboard(),
        disable_web_page_preview=True
    )


@router.message(F.text == "🔄 Восстановить пароль")
async def recover_password(message: Message):
    await message.answer(
        "🔄 <b>Восстановление пароля</b>\n\n"
        "1️⃣ proracers.by\n"
        "2️⃣ 'Забыли пароль?'\n"
        "3️⃣ Введите почту\n\n"
        "✅ Если не приходит письмо — нажмите '🆘 Оператор срочно'.",
        parse_mode="HTML",
        reply_markup=get_access_keyboard(),
        disable_web_page_preview=True
    )


# ============ КАТЕГОРИЯ: ТЕХПОДДЕРЖКА ============

@router.message(F.text == "🔧 Техподдержка")
async def tech_support_category(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    await message.answer(
        "🔧 <b>Выберите проблему:</b>\n\n"
        "• 📱 Проблема с приложением\n"
        "• 🚫 Нет заказов\n"
        "• ⭐ Упал рейтинг",
        parse_mode="HTML",
        reply_markup=get_support_keyboard()
    )


@router.message(F.text == "📱 Проблема с приложением")
async def app_problem(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    driver_name = user.get('fullname', 'водитель')
    driver_id = user.get('driver_id', 'не указан')
    
    title = f"📱 Проблема с приложением: {driver_name} (ID: {driver_id})"
    success = await create_task_via_webhook(title, "Проблема с приложением Яндекс Про")
    
    if success:
        await message.answer(
            "📱 <b>Заявка создана!</b>\n\nПопробуйте перезагрузить приложение.",
            parse_mode="HTML",
            reply_markup=get_support_keyboard()
        )
    else:
        await message.answer("❌ Ошибка.", reply_markup=get_support_keyboard())


@router.message(F.text == "🚫 Нет заказов")
async def no_orders(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    driver_name = user.get('fullname', 'водитель')
    driver_id = user.get('driver_id', 'не указан')
    
    title = f"🚫 Нет заказов: {driver_name} (ID: {driver_id})"
    success = await create_task_via_webhook(title, "Проблема с заказами")
    
    if success:
        await message.answer(
            "🚕 <b>Заявка создана!</b>\n\nПроверим ваш аккаунт.",
            parse_mode="HTML",
            reply_markup=get_support_keyboard()
        )
    else:
        await message.answer("❌ Ошибка.", reply_markup=get_support_keyboard())


@router.message(F.text == "⭐ Упал рейтинг")
async def rating_dropped(message: Message, state: FSMContext):
    user = await check_registration(message, state)
    if not user:
        return
    
    driver_name = user.get('fullname', 'водитель')
    driver_id = user.get('driver_id', 'не указан')
    
    title = f"⭐ Вопрос по рейтингу: {driver_name} (ID: {driver_id})"
    success = await create_task_via_webhook(title, "Вопрос о падении рейтинга")
    
    if success:
        await message.answer(
            "⭐ <b>Заявка создана!</b>\n\nСпециалист даст рекомендации.",
            parse_mode="HTML",
            reply_markup=get_support_keyboard()
        )
    else:
        await message.answer("❌ Ошибка.", reply_markup=get_support_keyboard())


# ============ ОБРАБОТЧИК ИИ (с проверкой регистрации) ============

# Список кнопок, которые НЕ обрабатываем
IGNORED_BUTTONS = [
    "📝 Зарегистрироваться", "⛽ Топливная карта", "💵 Выплаты и зарплата",
    "🔐 Доступ к сайту", "🔧 Техподдержка", "◀️ Назад", "❓ Помощь",
    "📞 Оператор", "🆘 Оператор срочно", "🆔 Мой профиль",
    "🔓 Разблокировать карту", "📈 Обновить лимит", "⛽ Не работает на заправке",
    "🆕 Заказать новую карту", "💰 Вывести деньги на карту", "❓ Где мои деньги?",
    "📈 Увеличить квоту", "💳 Ошибка в реквизитах", "🔓 Открыть доступ",
    "📝 Зарегистрироваться на сайте", "🔄 Восстановить пароль", "📱 Проблема с приложением",
    "🚫 Нет заказов", "⭐ Упал рейтинг"
]


@router.message(F.text, ~F.text.in_(IGNORED_BUTTONS))
async def handle_ai_message(message: Message, state: FSMContext):
    """Обработка текстовых сообщений через ИИ (кроме кнопок и регистрации)"""
    text = message.text.strip()
    
    # Пропускаем команды
    if text.startswith('/'):
        return
    
    # Проверяем, не идёт ли регистрация
    current_state = await state.get_state()
    if current_state and "RegistrationStates" in current_state:
        logger.info(f"⏭️ Пропускаем сообщение, идёт регистрация: {current_state}")
        return
    
    # Проверяем регистрацию через БД
    user = await check_registration(message, state)
    if not user:
        return
    
    driver_name = user.get('fullname', 'водитель')
    driver_id = user.get('driver_id', 'не указан')
    
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    result = await llm_classifier.classify(text)
    
    if result.get("need_manager"):
        title = f"{result.get('category')}: {result.get('problem')} - {driver_name} (ID: {driver_id})"
        description = f"""
Сообщение: {text}
Категория: {result.get('category')}
Проблема: {result.get('problem')}
Водитель: {driver_name}
ID: {driver_id}
        """
        success = await create_task_via_webhook(title, description)
        
        if success:
            await message.answer(
                f"{result.get('response')}\n\n✅ Заявка создана!",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                f"{result.get('response')}\n\n⚠️ Ошибка. Нажмите '🆘 Оператор срочно'.",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
    else:
        await message.answer(
            f"{result.get('response')}\n\n{result.get('solution')}",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )