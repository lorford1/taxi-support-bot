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

# Создаём роутер
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
        print(f"Ошибка вебхука: {e}")
        return False


# ============ ОБРАБОТЧИК СРОЧНОГО ОПЕРАТОРА ============

@router.message(F.text == "🆘 Оператор срочно")
async def urgent_operator_start(message: Message, state: FSMContext):
    """Начало срочного вызова оператора — запрос сообщения"""
    user_data = await state.get_data()
    
    if not user_data.get("registered"):
        await message.answer(
            "❌ Сначала зарегистрируйтесь (кнопка 📝 Зарегистрироваться или /reg)",
            reply_markup=get_unregistered_keyboard()
        )
        return
    
    driver_name = user_data.get('fullname', message.from_user.full_name)
    
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
        "/start — главное менú\n"
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
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', message.from_user.full_name)
    driver_id = user_data.get('driver_id', 'не указан')
    
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
    user_data = await state.get_data()
    
    if not user_data.get("registered"):
        await message.answer(
            "❌ Сначала зарегистрируйтесь (/reg)",
            reply_markup=get_unregistered_keyboard()
        )
        return
    
    await message.answer(
        f"⛽ <b>Выберите проблему:</b>\n\n"
        f"👤 {user_data.get('fullname')}\n\n"
        "• 🔓 Разблокировать карту\n"
        "• 📈 Обновить лимит\n"
        "• ⛽ Не работает на заправке\n"
        "• 🆕 Заказать новую карту",
        parse_mode="HTML",
        reply_markup=get_fuel_card_keyboard()
    )


@router.message(F.text == "🔓 Разблокировать карту")
async def unblock_card(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
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
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
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
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
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
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    
    await message.answer(
        f"🆕 <b>{driver_name}, заказать новую карту</b>\n\n"
        f"🔗 Ссылка: <code>https://proracers.by/bncard</code>\n\n"
        f"💡 Если не пришло SMS — нажмите '🆘 Оператор срочно'.",
        parse_mode="HTML",
        reply_markup=get_fuel_card_keyboard(),
        disable_web_page_preview=True
    )


# ============ ОБРАБОТЧИК ИИ (только для зарегистрированных, не во время регистрации) ============

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
    """Обработка текстовых сообщений через ИИ (кроме кнопок)"""
    text = message.text.strip()
    
    # Пропускаем команды
    if text.startswith('/'):
        return
    
    # Пропускаем, если пользователь в процессе регистрации
    current_state = await state.get_state()
    if current_state and "RegistrationStates" in current_state:
        return
    
    user_data = await state.get_data()
    
    if not user_data.get("registered"):
        await message.answer(
            "❌ Сначала зарегистрируйтесь: /reg",
            reply_markup=get_unregistered_keyboard()
        )
        return
    
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
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