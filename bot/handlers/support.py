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


@router.message(Command("cancel"))
async def cancel_urgent(message: Message, state: FSMContext):
    """Отмена срочного вызова"""
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


# ============ ОСНОВНЫЕ КОМАНДЫ ============

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    user = user_storage.get_user(telegram_id)
    
    if user:
        await message.answer(
            f"🚕 <b>С возвращением, {user.get('fullname')}!</b>\n\n"
            f"🆔 Ваш ID: <code>{user.get('driver_id')}</code>\n\n"
            f"Выберите категорию проблемы на кнопках ниже.\n\n"
            f"💡 <b>Совет:</b> Вы можете просто написать проблему словами,\n"
            f"и я постараюсь помочь или создам заявку.",
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
            "Нажмите на кнопку <b>📝 Зарегистрироваться</b>.",
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
        "/cancel — отмена текущего действия",
        parse_mode="HTML"
    )


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
            "❌ Сначала зарегистрируйтесь (кнопка 📝 Зарегистрироваться)",
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


@router.message(F.text == "📈 Обновить лимит")
async def update_limit(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    title = f"📈 Обновление лимита: {driver_name} (ID: {driver_id})"
    description = f"Запрос на обновление лимита топливной карты\nВодитель: {driver_name}\nID: {driver_id}"
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            f"📈 <b>Хорошо, {driver_name}!</b>\n\n"
            f"✅ Создана заявка на обновление лимита.\n\n"
            f"⛽ Лимит будет обновлён в ближайшее время.",
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
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    title = f"⛽ Проблема на заправке: {driver_name} (ID: {driver_id})"
    description = f"Водитель сообщает, что карта не работает на заправке\nВодитель: {driver_name}\nID: {driver_id}"
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            f"⛽ <b>Понимаю вашу ситуацию, {driver_name}!</b>\n\n"
            f"✅ Создана заявка в техподдержку.\n\n"
            f"🛠️ Специалист проверит статус вашей карты.",
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
        f"🆕 <b>{driver_name}, заказать новую топливную карту</b>\n\n"
        f"🔗 Ссылка для заказа: <code>https://proracers.by/bncard</code>\n\n"
        f"📌 <b>После заказа:</b>\n"
        f"• На ваш номер телефона придёт SMS с данными карты\n"
        f"• Скачайте приложение BNCard для активации\n"
        f"• Настройте типы топлива по ссылке: <code>https://proracers.by/fc-tuning</code>\n\n"
        f"💡 Если SMS не пришло в течение часа — нажмите '🆘 Оператор срочно'.",
        parse_mode="HTML",
        reply_markup=get_fuel_card_keyboard(),
        disable_web_page_preview=True
    )


# ============ КАТЕГОРИЯ: ВЫПЛАТЫ И ЗАРПЛАТА ============

@router.message(F.text == "💵 Выплаты и зарплата")
async def payments_category(message: Message, state: FSMContext):
    user_data = await state.get_data()
    
    if not user_data.get("registered"):
        await message.answer("❌ Сначала зарегистрируйтесь", reply_markup=get_unregistered_keyboard())
        return
    
    await message.answer(
        f"💵 <b>Выберите проблему с выплатами</b>\n\n"
        f"👤 Водитель: {user_data.get('fullname')}\n\n"
        "• 💰 Вывести деньги на карту\n"
        "• ❓ Где мои деньги?\n"
        "• 📈 Увеличить квоту\n"
        "• 💳 Ошибка в реквизитах\n\n"
        "💡 <b>Или просто напишите</b> — я помогу!",
        parse_mode="HTML",
        reply_markup=get_payments_keyboard()
    )


@router.message(F.text == "💰 Вывести деньги на карту")
async def withdraw_money(message: Message):
    await message.answer(
        "💰 <b>Инструкция по выводу денег на карту</b>\n\n"
        "1️⃣ Перейдите на сайт: <code>https://proracers.by/exchange</code>\n"
        "2️⃣ Укажите сумму вывода\n"
        "3️⃣ Введите IBAN вашей карты\n"
        "4️⃣ Укажите ФИО владельца карты\n\n"
        "⏰ Деньги поступают в рабочие дни до 14:00\n"
        "📧 На почту придёт подтверждение запроса\n\n"
        "💡 <b>Если нужна срочная помощь</b> — нажмите '🆘 Оператор срочно'",
        parse_mode="HTML",
        reply_markup=get_payments_keyboard(),
        disable_web_page_preview=True
    )


@router.message(F.text == "❓ Где мои деньги?")
async def where_is_money(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    title = f"💰 Проверка выплаты: {driver_name} (ID: {driver_id})"
    description = f"Запрос на проверку статуса выплаты\nВодитель: {driver_name}\nID: {driver_id}"
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            "🔍 <b>Проверка статуса выплаты</b>\n\n"
            "✅ Заявка создана\n\n"
            "⏰ Обычно деньги поступают в течение рабочего дня.\n"
            "📞 Если прошло более 3 дней — нажмите '🆘 Оператор срочно'.",
            parse_mode="HTML",
            reply_markup=get_payments_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка. Нажмите '🆘 Оператор срочно'.",
            reply_markup=get_payments_keyboard()
        )


@router.message(F.text == "📈 Увеличить квоту")
async def increase_quota(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    title = f"📈 Увеличение квоты: {driver_name} (ID: {driver_id})"
    description = f"Запрос на увеличение квоты вывода средств\nВодитель: {driver_name}\nID: {driver_id}"
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            "📈 <b>Увеличение квоты на вывод</b>\n\n"
            "✅ Заявка создана\n\n"
            "👨‍💼 Менеджер свяжется с вами для уточнения деталей.\n"
            "📊 Квота обновляется раз в неделю.\n\n"
            "💡 <b>Если срочно</b> — нажмите '🆘 Оператор срочно'",
            parse_mode="HTML",
            reply_markup=get_payments_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка. Нажмите '🆘 Оператор срочно'.",
            reply_markup=get_payments_keyboard()
        )


@router.message(F.text == "💳 Ошибка в реквизитах")
async def wrong_details(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    title = f"💳 Ошибка в реквизитах: {driver_name} (ID: {driver_id})"
    description = f"Запрос на проверку реквизитов карты\nВодитель: {driver_name}\nID: {driver_id}"
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            "💳 <b>Ошибка в реквизитах карты</b>\n\n"
            "✅ Заявка создана\n\n"
            "Проверьте правильность ввода:\n"
            "• IBAN должен содержать только буквы и цифры\n"
            "• ФИО должно быть на русском языке\n\n"
            "💡 <b>Если нужна помощь</b> — нажмите '🆘 Оператор срочно'",
            parse_mode="HTML",
            reply_markup=get_payments_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка. Нажмите '🆘 Оператор срочно'.",
            reply_markup=get_payments_keyboard()
        )


# ============ КАТЕГОРИЯ: ДОСТУП К САЙТУ ============

@router.message(F.text == "🔐 Доступ к сайту")
async def access_category(message: Message, state: FSMContext):
    user_data = await state.get_data()
    
    if not user_data.get("registered"):
        await message.answer("❌ Сначала зарегистрируйтесь", reply_markup=get_unregistered_keyboard())
        return
    
    await message.answer(
        f"🔐 <b>Выберите проблему с доступом</b>\n\n"
        f"👤 Водитель: {user_data.get('fullname')}\n\n"
        "• 🔓 Открыть доступ\n"
        "• 📝 Зарегистрироваться на сайте\n"
        "• 🔄 Восстановить пароль\n\n"
        "💡 <b>Или просто напишите</b> — я помогу!",
        parse_mode="HTML",
        reply_markup=get_access_keyboard()
    )


@router.message(F.text == "🔓 Открыть доступ")
async def open_access(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    title = f"🔐 Запрос доступа: {driver_name} (ID: {driver_id})"
    description = f"Запрос на открытие доступа к сайту\nВодитель: {driver_name}\nID: {driver_id}"
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            "🔐 <b>Доступ к сайту</b>\n\n"
            "✅ Доступ предоставлен!\n\n"
            "🌐 Войдите на сайт: <code>https://proracers.by</code>\n"
            "📧 Используйте вашу почту для входа.\n\n"
            "💡 Если не можете войти — нажмите '🆘 Оператор срочно'.",
            parse_mode="HTML",
            reply_markup=get_access_keyboard(),
            disable_web_page_preview=True
        )
    else:
        await message.answer(
            f"❌ Ошибка. Нажмите '🆘 Оператор срочно'.",
            reply_markup=get_access_keyboard()
        )


@router.message(F.text == "📝 Зарегистрироваться на сайте")
async def register_site(message: Message):
    await message.answer(
        "📝 <b>Регистрация на сайте</b>\n\n"
        "1️⃣ Перейдите на сайт: <code>https://proracers.by</code>\n"
        "2️⃣ Нажмите 'Регистрация'\n"
        "3️⃣ Укажите вашу почту (Gmail)\n"
        "4️⃣ Заполните ФИО и ID\n"
        "5️⃣ Подтвердите регистрацию по ссылке в письме\n\n"
        "✅ <b>После регистрации напишите сюда</b> — я выдам доступ.\n\n"
        "💡 Если письмо не пришло — проверьте папку Спам.",
        parse_mode="HTML",
        reply_markup=get_access_keyboard(),
        disable_web_page_preview=True
    )


@router.message(F.text == "🔄 Восстановить пароль")
async def recover_password(message: Message):
    await message.answer(
        "🔄 <b>Восстановление пароля</b>\n\n"
        "1️⃣ Перейдите на страницу входа: <code>https://proracers.by</code>\n"
        "2️⃣ Нажмите 'Забыли пароль?'\n"
        "3️⃣ Введите вашу почту\n"
        "4️⃣ Следуйте инструкциям в письме\n\n"
        "✅ Если не приходит письмо — нажмите '🆘 Оператор срочно'.",
        parse_mode="HTML",
        reply_markup=get_access_keyboard(),
        disable_web_page_preview=True
    )


# ============ КАТЕГОРИЯ: ТЕХПОДДЕРЖКА ============

@router.message(F.text == "🔧 Техподдержка")
async def tech_support_category(message: Message, state: FSMContext):
    user_data = await state.get_data()
    
    if not user_data.get("registered"):
        await message.answer("❌ Сначала зарегистрируйтесь", reply_markup=get_unregistered_keyboard())
        return
    
    await message.answer(
        f"🔧 <b>Выберите техническую проблему</b>\n\n"
        f"👤 Водитель: {user_data.get('fullname')}\n\n"
        "• 📱 Проблема с приложением\n"
        "• 🚫 Нет заказов\n"
        "• ⭐ Упал рейтинг\n\n"
        "💡 <b>Или просто напишите</b> — я помогу!",
        parse_mode="HTML",
        reply_markup=get_support_keyboard()
    )


@router.message(F.text == "📱 Проблема с приложением")
async def app_problem(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    title = f"📱 Проблема с приложением: {driver_name} (ID: {driver_id})"
    description = f"Запрос о проблеме с приложением Яндекс Про\nВодитель: {driver_name}\nID: {driver_id}"
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            "📱 <b>Проблема с приложением Яндекс Про</b>\n\n"
            "✅ Заявка создана\n\n"
            "💡 Попробуйте:\n"
            "• Перезагрузить приложение\n"
            "• Очистить кэш\n"
            "• Переустановить приложение\n\n"
            "🛠️ Специалист проверит ваш аккаунт.\n\n"
            "💡 <b>Если срочно</b> — нажмите '🆘 Оператор срочно'",
            parse_mode="HTML",
            reply_markup=get_support_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка. Нажмите '🆘 Оператор срочно'.",
            reply_markup=get_support_keyboard()
        )


@router.message(F.text == "🚫 Нет заказов")
async def no_orders(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    title = f"🚫 Нет заказов: {driver_name} (ID: {driver_id})"
    description = f"Запрос о проблеме отсутствия заказов\nВодитель: {driver_name}\nID: {driver_id}"
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            "🚕 <b>Нет заказов</b>\n\n"
            "✅ Заявка создана\n\n"
            "💡 Возможные причины:\n"
            "• Низкий рейтинг (ниже 4.5)\n"
            "• Часы низкой активности\n"
            "• Технические работы\n\n"
            "👨‍💼 Менеджер свяжется с вами.\n\n"
            "💡 <b>Если срочно</b> — нажмите '🆘 Оператор срочно'",
            parse_mode="HTML",
            reply_markup=get_support_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка. Нажмите '🆘 Оператор срочно'.",
            reply_markup=get_support_keyboard()
        )


@router.message(F.text == "⭐ Упал рейтинг")
async def rating_dropped(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    title = f"⭐ Вопрос по рейтингу: {driver_name} (ID: {driver_id})"
    description = f"Запрос о падении рейтинга водителя\nВодитель: {driver_name}\nID: {driver_id}"
    
    success = await create_task_via_webhook(title, description)
    
    await status_msg.delete()
    
    if success:
        await message.answer(
            "⭐ <b>Вопросы по рейтингу</b>\n\n"
            "✅ Заявка создана\n\n"
            "💡 Рейтинг зависит от:\n"
            "• Оценок пассажиров\n"
            "• Процента принятых заказов\n"
            "• Отмен и опозданий\n\n"
            "👨‍💼 Специалист даст рекомендации.\n\n"
            "💡 <b>Если срочно</b> — нажмите '🆘 Оператор срочно'",
            parse_mode="HTML",
            reply_markup=get_support_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка. Нажмите '🆘 Оператор срочно'.",
            reply_markup=get_support_keyboard()
        )


# ============ ОБРАБОТЧИК ЛЮБЫХ ТЕКСТОВЫХ СООБЩЕНИЙ (ИИ) ============

@router.message(F.text)
async def handle_any_text(message: Message, state: FSMContext):
    """Обработка любых текстовых сообщений через ИИ"""
    text = message.text.strip()
    
    # Пропускаем команды
    if text.startswith('/'):
        return
    
    # Список кнопок, которые не нужно обрабатывать ИИ
    buttons = ["⛽ Топливная карта", "💵 Выплаты и зарплата", "🔐 Доступ к сайту", 
               "🔧 Техподдержка", "◀️ Назад", "❓ Помощь", "📞 Оператор", 
               "🆘 Оператор срочно", "🆔 Мой профиль", "📝 Зарегистрироваться",
               "🔓 Разблокировать карту", "📈 Обновить лимит", "⛽ Не работает на заправке",
               "🆕 Заказать новую карту", "💰 Вывести деньги на карту", "❓ Где мои деньги?",
               "📈 Увеличить квоту", "💳 Ошибка в реквизитах", "🔓 Открыть доступ",
               "📝 Зарегистрироваться на сайте", "🔄 Восстановить пароль", "📱 Проблема с приложением",
               "🚫 Нет заказов", "⭐ Упал рейтинг"]
    
    if text in buttons:
        return
    
    user_data = await state.get_data()
    
    if not user_data.get("registered"):
        await message.answer(
            "❌ Сначала зарегистрируйтесь (кнопка 📝 Зарегистрироваться)",
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
        # Создаём задачу в Planfix через вебхук
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