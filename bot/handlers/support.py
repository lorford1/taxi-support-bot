from aiogram import Router, F
from aiogram.filters import Command
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
from storage.user_storage import user_storage
from core.planfix_client import planfix

# Создаём роутер
router = Router()

# Клавиатуры
def get_registered_keyboard():
    from bot.handlers.registration import get_registered_keyboard as grk
    return grk()

def get_unregistered_keyboard():
    from bot.handlers.registration import get_unregistered_keyboard as guk
    return guk()


# База готовых ответов
ANSWERS = {
    "разблокировать карту": "🔓 Хорошо, {name}, я создал заявку на разблокировку вашей топливной карты.\n\n✅ Номер заявки: #{}\n\n⏱️ Обычно занимает до 30 минут.",
    "обновить лимит": "📈 Я отправил запрос на увеличение лимита.\n\n✅ Номер заявки: #{}",
    "вывести деньги": "💰 Для вывода денег на карту:\n\n1️⃣ Перейдите на сайт: proracers.by/exchange\n2️⃣ Укажите IBAN вашей карты\n3️⃣ Укажите ФИО владельца",
    "где мои деньги": "🔍 Проверяю ваш запрос. Деньги обычно поступают в течение рабочего дня.\n\n✅ Номер заявки: #{}",
}


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    telegram_id = str(message.from_user.id)
    user = user_storage.get_user(telegram_id)
    
    if user:
        # Уже зарегистрирован
        await message.answer(
            f"🚕 <b>С возвращением, {user.get('fullname')}!</b>\n\n"
            f"🆔 Ваш ID: <code>{user.get('driver_id')}</code>\n\n"
            f"Выберите категорию проблемы на кнопках ниже.",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
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
        "<b>Команды:</b>\n"
        "/start — главное меню\n"
        "/help — эта справка\n\n"
        "📞 <b>Оператор</b> — связь с живым специалистом",
        parse_mode="HTML"
    )


@router.message(F.text == "◀️ Назад")
async def back_to_main(message: Message):
    await message.answer(
        "🏠 Главное меню. Выберите категорию:",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "⛽ Топливная карта")
async def fuel_card_category(message: Message, state: FSMContext):
    """Категория топливной карты"""
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
        "• Разблокировать карту\n"
        "• Обновить лимит\n"
        "• Не работает на заправке\n"
        "• Заказать новую карту",
        parse_mode="HTML",
        reply_markup=get_fuel_card_keyboard()
    )


@router.message(F.text == "💵 Выплаты и зарплата")
async def payments_category(message: Message, state: FSMContext):
    user_data = await state.get_data()
    
    if not user_data.get("registered"):
        await message.answer("❌ Сначала зарегистрируйтесь", reply_markup=get_unregistered_keyboard())
        return
    
    await message.answer(
        "💵 <b>Выберите проблему с выплатами</b>\n\n"
        "• Вывести деньги на карту — инструкция\n"
        "• Где мои деньги? — проверка статуса\n"
        "• Увеличить квоту — если превышен лимит",
        parse_mode="HTML",
        reply_markup=get_payments_keyboard()
    )


@router.message(F.text == "🔐 Доступ к сайту")
async def access_category(message: Message, state: FSMContext):
    user_data = await state.get_data()
    
    if not user_data.get("registered"):
        await message.answer("❌ Сначала зарегистрируйтесь", reply_markup=get_unregistered_keyboard())
        return
    
    await message.answer(
        "🔐 <b>Выберите проблему с доступом</b>\n\n"
        "• Открыть доступ — если нет входа\n"
        "• Зарегистрироваться — если нет аккаунта\n"
        "• Восстановить пароль — если забыли",
        parse_mode="HTML",
        reply_markup=get_access_keyboard()
    )


@router.message(F.text == "🔧 Техподдержка")
async def tech_support_category(message: Message, state: FSMContext):
    user_data = await state.get_data()
    
    if not user_data.get("registered"):
        await message.answer("❌ Сначала зарегистрируйтесь", reply_markup=get_unregistered_keyboard())
        return
    
    await message.answer(
        "🔧 <b>Выберите техническую проблему</b>\n\n"
        "• Проблема с приложением — лагает, вылетает\n"
        "• Нет заказов — долго нет заказов\n"
        "• Упал рейтинг — вопросы по рейтингу",
        parse_mode="HTML",
        reply_markup=get_support_keyboard()
    )


@router.message(F.text == "📞 Оператор")
async def call_operator(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', message.from_user.full_name)
    driver_id = user_data.get('driver_id', 'не указан')
    
    result = await planfix.create_task(
        title=f"🚨 Срочный вызов оператора: {driver_name}",
        description=f"""
Пользователь запросил соединение с оператором.

👤 Водитель: {driver_name}
🆔 ID: {driver_id}
📅 Время: {message.date}
        """
    )
    
    if result.get("success"):
        await message.answer(
            "👨‍💼 <b>Соединяю с оператором...</b>\n\n"
            f"✅ Создана заявка №{result.get('general')}\n\n"
            "Специалист свяжется с вами в ближайшее время.",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "👨‍💼 Создана заявка оператору. Специалист свяжется с вами."
        )


@router.message(F.text == "❓ Помощь")
async def help_button(message: Message):
    await cmd_help(message)


@router.message(F.text == "🔓 Разблокировать карту")
async def unblock_card(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    
    result = await planfix.create_task(
        title=f"⛽ Разблокировка карты: {driver_name}",
        description=f"Запрос на разблокировку топливной карты от {driver_name}"
    )
    
    if result.get("success"):
        await message.answer(
            ANSWERS["разблокировать карту"].format(driver_name, result.get('general')),
            reply_markup=get_fuel_card_keyboard()
        )
    else:
        await message.answer("⛽ Создал заявку на разблокировку.")


@router.message(F.text == "💰 Вывести деньги на карту")
async def withdraw_money(message: Message):
    await message.answer(
        ANSWERS["вывести деньги"],
        reply_markup=get_payments_keyboard()
    )


@router.message(F.text == "❓ Где мои деньги?")
async def where_is_money(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    
    result = await planfix.create_task(
        title=f"💰 Проверка выплаты: {driver_name}",
        description=f"Запрос на проверку статуса выплаты"
    )
    
    await message.answer(
        ANSWERS["где мои деньги"].format(result.get('general', 'создана')),
        reply_markup=get_payments_keyboard()
    )


@router.message(F.text == "🔓 Открыть доступ")
async def open_access(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    
    await planfix.create_task(
        title=f"🔐 Запрос доступа: {driver_name}",
        description=f"Запрос на открытие доступа к сайту"
    )
    
    await message.answer(
        "🔐 Доступ к сайту предоставлен!\n\n🌐 Войдите по ссылке: proracers.by",
        reply_markup=get_access_keyboard()
    )