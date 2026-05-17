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
            "❌ Сначала зарегистрируйтесь (кнопка 📝 Зарегистрироваться)",
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
        f"<i>Пример: \"У меня заблокировалась топливная карта на заправке, не могу заправиться, нужна срочная помощь\"</i>\n\n"
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
            "❌ Пожалуйста, напишите более подробное сообщение (минимум 5 символов).\n\n"
            "Опишите вашу проблему:",
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
            f"📅 Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"👨‍💼 <b>Оператор свяжется с вами в ближайшее время!</b>\n\n"
            f"📌 <i>Пожалуйста, оставайтесь на связи.</i>",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            f"❌ <b>Ошибка при отправке срочного запроса!</b>\n\n"
            f"Пожалуйста, напишите '📞 Оператор' для связи со специалистом.",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
    
    await state.clear()


# ============ ОБРАБОТЧИК КОМАНД ============

@router.message(Command("cancel"))
async def cancel_action(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    current_state = await state.get_state()
    
    if current_state == UrgentOperatorStates.waiting_for_message:
        await message.answer(
            "❌ Срочный вызов отменён.\n\n"
            "Вы можете вернуться в главное меню, нажав /start",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
    else:
        await message.answer(
            "❌ Нет активных действий для отмены.",
            reply_markup=get_main_keyboard()
        )


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    user = user_storage.get_user(telegram_id)
    
    if user:
        await message.answer(
            f"🚕 <b>С возвращением, {user.get('fullname')}!</b>\n\n"
            f"🆔 Ваш ID: <code>{user.get('driver_id')}</code>\n\n"
            f"Выберите категорию проблемы на кнопках ниже.\n\n"
            f"💡 <b>Совет:</b> Вы можете просто написать проблему словами.",
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
        "2️⃣ Выберите конкретную проблему\n"
        "3️⃣ Бот создаст заявку и даст ответ\n\n"
        "<b>Или просто напишите проблему словами!</b>\n"
        "Например: 'У меня не пришли деньги на карту'\n\n"
        "<b>Срочный вызов оператора:</b>\n"
        "🆘 Нажмите 'Оператор срочно' → напишите сообщение\n\n"
        "<b>Команды:</b>\n"
        "/start — главное меню\n"
        "/help — эта справка\n"
        "/reg — зарегистрироваться\n"
        "/cancel — отмена текущего действия",
        parse_mode="HTML"
    )


# ============ НАВИГАЦИЯ ============

@router.message(F.text == "◀️ Назад")
async def back_to_main(message: Message):
    await message.answer(
        "🏠 <b>Главное меню</b>\n\nВыберите категорию или напишите проблему:",
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
    
    status_msg = await message.answer("🔄 Создаю заявку оператору...")
    
    title = f"📞 Вызов оператора: {driver_name} (ID: {driver_id})"
    description = f"""
Пользователь запросил соединение с оператором.

👤 Водитель: {driver_name}
🆔 ID: {driver_id}
📅 Время: {message.date}
🆔 Telegram ID: {message.from_user.id}
    """
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            f"👨‍💼 <b>Соединяю с оператором...</b>\n\n"
            f"✅ Заявка создана в Planfix\n\n"
            f"Специалист свяжется с вами в ближайшее время.",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"❌ <b>Ошибка при создании заявки!</b>\n\n"
            f"Пожалуйста, нажмите '🆘 Оператор срочно'.",
            parse_mode="HTML"
        )


# ============ КАТЕГОРИЯ: ТОПЛИВНАЯ КАРТА ============

@router.message(F.text == "⛽ Топливная карта")
async def fuel_card_category(message: Message, state: FSMContext):
    user_data = await state.get_data()
    
    if not user_data.get("registered"):
        await message.answer(
            "❌ Сначала зарегистрируйтесь (кнопка 📝 Зарегистрироваться или /reg)",
            reply_markup=get_unregistered_keyboard()
        )
        return
    
    await message.answer(
        f"⛽ <b>Выберите проблему с топливной картой</b>\n\n"
        f"👤 Водитель: {user_data.get('fullname')}\n\n"
        "• 🔓 Разблокировать карту\n"
        "• 📈 Обновить лимит\n"
        "• ⛽ Не работает на заправке\n"
        "• 🆕 Заказать новую карту\n\n"
        "💡 <b>Или просто напишите проблему</b> — я пойму!",
        parse_mode="HTML",
        reply_markup=get_fuel_card_keyboard()
    )


@router.message(F.text == "🔓 Разблокировать карту")
async def unblock_card(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    title = f"⛽ Разблокировка карты: {driver_name} (ID: {driver_id})"
    description = f"""
Запрос на разблокировку топливной карты

👤 Водитель: {driver_name}
🆔 ID: {driver_id}
📅 Время: {message.date}
    """
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            f"🔓 <b>Хорошо, {driver_name}!</b>\n\n"
            f"✅ Заявка создана в Planfix!\n\n"
            f"👨‍💼 Специалист свяжется с вами.\n\n"
            f"💡 <b>Если ситуация срочная</b> — нажмите '🆘 Оператор срочно'",
            parse_mode="HTML",
            reply_markup=get_fuel_card_keyboard()
        )
    else:
        await message.answer(
            f"❌ <b>Ошибка при создании заявки!</b>\n\n"
            f"Пожалуйста, нажмите '🆘 Оператор срочно'.",
            parse_mode="HTML",
            reply_markup=get_fuel_card_keyboard()
        )


# ============ ОСТАЛЬНЫЕ ОБРАБОТЧИКИ КАТЕГОРИЙ ============
# (здесь идут остальные обработчики для выплат, доступа, техподдержки...)
# Они остаются без изменений, просто убедитесь, что они есть


# ============ ОБРАБОТЧИК ИИ ДЛЯ ОБЫЧНЫХ СООБЩЕНИЙ ============
# Важно: этот обработчик НЕ перехватывает кнопки!

# Список кнопок, которые НЕ нужно обрабатывать ИИ
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
    """Обработка обычных текстовых сообщений через ИИ (кроме кнопок)"""
    text = message.text.strip()
    
    # Пропускаем команды
    if text.startswith('/'):
        return
    
    user_data = await state.get_data()
    
    if not user_data.get("registered"):
        await message.answer(
            "❌ Сначала зарегистрируйтесь (кнопка 📝 Зарегистрироваться или /reg)",
            reply_markup=get_unregistered_keyboard()
        )
        return
    
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
    # Отправляем статус "печатает"
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    # Используем ИИ для анализа
    result = await llm_classifier.classify(text)
    
    if result.get("need_manager"):
        title = f"{result.get('category')}: {result.get('problem')} - {driver_name} (ID: {driver_id})"
        description = f"""
Сообщение: {text}

Категория: {result.get('category')}
Проблема: {result.get('problem')}
Решение: {result.get('solution')}

👤 Водитель: {driver_name}
🆔 ID: {driver_id}
📅 Время: {message.date}
        """
        success = await create_task_via_webhook(title, description)
        
        if success:
            await message.answer(
                f"{result.get('response')}\n\n✅ Заявка создана в Planfix!",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                f"{result.get('response')}\n\n⚠️ Ошибка при создании заявки. Нажмите '🆘 Оператор срочно'.",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
    else:
        await message.answer(
            f"{result.get('response')}\n\n{result.get('solution')}",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )