import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
import aiohttp

from bot.keyboards.menu import get_registered_keyboard, get_unregistered_keyboard
from storage.user_storage import user_storage
from core.llm_intent import llm_classifier

logger = logging.getLogger(__name__)
router = Router()

# URL вебхука Planfix
WEBHOOK_URL = "https://taxit.planfix.ru/webhook/get/j0tc-k18j-5jf6-bqvh"
PROJECT_ID = None

# ID оператора в Telegram (замените на реальный)
OPERATOR_TELEGRAM_ID = 1914378378  # Ваш Telegram ID


async def create_task_via_webhook(title: str, description: str, chat_id: int = None) -> bool:
    """Создание задачи через входящий вебхук Planfix"""
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    full_description = description
    if chat_id:
        full_description = f"{description}\n\n📱 Telegram Chat ID: {chat_id}"
    
    params = {
        "name": title,
        "description": full_description,
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


# ============ ОСНОВНЫЕ КОМАНДЫ ============

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    telegram_id = str(message.from_user.id)
    user = user_storage.get_user(telegram_id)
    
    if user:
        fullname = user.get('fullname', 'Уважаемый водитель')
        name_parts = fullname.split()
        if len(name_parts) >= 2:
            first_name = name_parts[1]
        else:
            first_name = name_parts[0] if name_parts else "Уважаемый"
        
        await message.answer(
            f"🚕 <b>С возвращением, {fullname}!</b>\n\n"
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
            fullname=fullname,
            first_name=first_name,
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


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 <b>Как пользоваться ботом:</b>\n\n"
        "1️⃣ Зарегистрируйтесь (кнопка 📝 Зарегистрироваться)\n"
        "2️⃣ Напишите вашу проблему простыми словами\n"
        "3️⃣ Бот создаст заявку в Planfix\n\n"
        "<b>Примеры сообщений:</b>\n"
        "• Деньги не пришли на карту\n"
        "• Карта заблокировалась на заправке\n"
        "• Не могу зайти в личный кабинет\n\n"
        "<b>Команды:</b>\n"
        "/start — главное меню\n"
        "/help — эта справка",
        parse_mode="HTML"
    )


@router.message(F.text == "📞 Оператор")
async def call_operator(message: Message, state: FSMContext):
    """Срочный вызов оператора"""
    user_data = await state.get_data()
    
    if not user_data.get("registered"):
        await message.answer(
            "❌ Сначала зарегистрируйтесь (кнопка 📝 Зарегистрироваться)",
            reply_markup=get_unregistered_keyboard()
        )
        return
    
    driver_name = user_data.get('fullname', message.from_user.full_name)
    driver_id = user_data.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Создаю заявку оператору...")
    
    title = f"📞 Срочный вызов оператора: {driver_name} (ID: {driver_id})"
    description = f"""
👤 Водитель: {driver_name}
🆔 ID: {driver_id}
📅 Время: {message.date}
📱 Telegram ID: {message.from_user.id}

⚠️ Водитель запросил соединение с оператором!
    """
    
    success = await create_task_via_webhook(title, description, chat_id=message.chat.id)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            f"👨‍💼 <b>Заявка создана!</b>\n\nСпециалист свяжется с вами в ближайшее время.",
            parse_mode="HTML",
            reply_markup=get_registered_keyboard()
        )
        
        try:
            await message.bot.send_message(
                chat_id=OPERATOR_TELEGRAM_ID,
                text=f"🆕 <b>Срочный вызов оператора!</b>\n\n"
                     f"👤 {driver_name}\n"
                     f"🆔 ID: {driver_id}\n"
                     f"📋 Требуется внимание!",
                parse_mode="HTML"
            )
        except:
            pass
    else:
        await message.answer(
            f"❌ <b>Ошибка при создании заявки!</b>\n\n"
            f"Пожалуйста, попробуйте позже.",
            parse_mode="HTML",
            reply_markup=get_registered_keyboard()
        )


@router.message(F.text == "❓ Помощь")
async def help_button(message: Message):
    await cmd_help(message)


# ============ ОБРАБОТЧИК ОБЫЧНЫХ СООБЩЕНИЙ (для личных чатов с ботом) ============

@router.message(F.text)
async def handle_message(message: Message, state: FSMContext):
    """Обработка любого текстового сообщения в личном чате с ботом"""
    text = message.text.strip()
    
    # Пропускаем команды и кнопки
    if text.startswith('/'):
        return
    
    if text in ["❓ Помощь", "📞 Оператор", "📝 Зарегистрироваться"]:
        return
    
    user_data = await state.get_data()
    
    # Проверяем регистрацию
    if not user_data.get("registered"):
        telegram_id = str(message.from_user.id)
        user = user_storage.get_user(telegram_id)
        
        if not user:
            await message.answer(
                "❌ Сначала зарегистрируйтесь (кнопка 📝 Зарегистрироваться)",
                reply_markup=get_unregistered_keyboard()
            )
            return
        else:
            fullname = user.get('fullname', 'Уважаемый водитель')
            name_parts = fullname.split()
            if len(name_parts) >= 2:
                first_name = name_parts[1]
            else:
                first_name = name_parts[0] if name_parts else "Уважаемый"
            
            await state.update_data(
                driver_id=user.get('driver_id'),
                fullname=fullname,
                first_name=first_name,
                registered=True
            )
            user_data = await state.get_data()
    
    driver_name = user_data.get('fullname', 'водитель')
    driver_first_name = user_data.get('first_name', 'Уважаемый')
    driver_id = user_data.get('driver_id', 'не указан')
    
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    result = await llm_classifier.classify(text, driver_name=driver_first_name)
    
    if result.get("need_manager"):
        title = f"{result.get('category')}: {result.get('problem')} - {driver_name} (ID: {driver_id})"
        description = f"""
Сообщение: {text}
Категория: {result.get('category')}
Проблема: {result.get('problem')}
Решение: {result.get('solution')}
👤 Водитель: {driver_name}
🆔 ID: {driver_id}
        """
        success = await create_task_via_webhook(title, description, chat_id=message.chat.id)
        
        if success:
            await message.answer(
                f"{result.get('response')}\n\n✅ Заявка создана в Planfix!",
                parse_mode="HTML",
                reply_markup=get_registered_keyboard()
            )
        else:
            await message.answer(
                f"{result.get('response')}\n\n⚠️ Ошибка при создании заявки. Пожалуйста, нажмите '📞 Оператор'.",
                parse_mode="HTML",
                reply_markup=get_registered_keyboard()
            )
    else:
        await message.answer(
            result.get('response'),
            parse_mode="HTML",
            reply_markup=get_registered_keyboard()
        )


# ============ ОБРАБОТЧИК БИЗНЕС-СООБЩЕНИЙ (для Telegram Business) ============

@router.message(F.business_connection_id)
async def handle_business_message(message: Message, state: FSMContext):
    """Обработка сообщений, приходящих в бизнес-аккаунт Telegram"""
    
    business_conn_id = message.business_connection_id
    user_text = message.text
    
    if not user_text:
        return
    
    # Пробуем найти водителя по номеру телефона
    sender = message.from_user
    driver = None
    
    if sender.phone_number:
        # Ищем по номеру телефона (нужно добавить метод в user_storage)
        # driver = user_storage.get_user_by_phone(sender.phone_number)
        pass
    
    if not driver:
        driver_name = sender.full_name or sender.first_name or "водитель"
        await message.answer(
            f"🔐 Здравствуйте, {driver_name}! Для работы с поддержкой зарегистрируйтесь.\n"
            f"Отправьте ваш ID и ФИО боту @proracers_taxi_bot",
            business_connection_id=business_conn_id
        )
        return
    
    driver_name = driver.get('fullname', sender.full_name or sender.first_name or "водитель")
    name_parts = driver_name.split()
    first_name = name_parts[1] if len(name_parts) > 1 else name_parts[0]
    
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    result = await llm_classifier.classify(user_text, first_name)
    
    if result.get("need_manager"):
        title = f"{result.get('category')}: {result.get('problem')} - {driver_name}"
        description = f"""
Сообщение: {user_text}
Категория: {result.get('category')}
Проблема: {result.get('problem')}
Решение: {result.get('solution')}
Водитель: {driver_name}
        """
        success = await create_task_via_webhook(title, description)
        
        if success:
            await message.answer(
                f"{result.get('response')}\n\n✅ Заявка создана в Planfix!",
                business_connection_id=business_conn_id
            )
        else:
            await message.answer(
                f"{result.get('response')}\n\n⚠️ Ошибка при создании заявки. Пожалуйста, обратитесь к оператору.",
                business_connection_id=business_conn_id
            )
    else:
        await message.answer(
            result.get('response'),
            business_connection_id=business_conn_id
        )