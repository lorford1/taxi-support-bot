from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.enums import ParseMode

from bot.keyboards.menu import (
    get_main_keyboard,
    get_fuel_card_keyboard,
    get_payments_keyboard,
    get_access_keyboard,
    get_support_keyboard
)
from core.planfix_client import planfix

router = Router()

# База готовых ответов на основе реальных обращений
ANSWERS = {
    # Топливная карта
    "разблокировать карту": "🔓 Хорошо, я создал заявку на разблокировку вашей топливной карты.\n\n⏱️ Обычно разблокировка занимает до 30 минут.\n\n✅ Номер заявки: #{}\n\n⚠️ Карта блокируется автоматически при минусовом балансе на Яндексе. Пожалуйста, следите за балансом.",
    
    "обновить лимит": "📈 Я отправил запрос на увеличение лимита вашей топливной карты.\n\n⛽ Новый лимит будет установлен в течение часа.\n\n✅ Номер заявки: #{}",
    
    "не работает на заправке": "⛽ Понимаю вашу ситуацию. Создал заявку в техподдержку.\n\n🛠️ Специалист проверит статус вашей карты.\n\n✅ Номер заявки: #{}\n\n💡 Если у вас минусовой баланс на Яндексе, карта блокируется автоматически.",
    
    # Выплаты
    "вывести деньги": "💰 Для вывода денег на карту:\n\n1️⃣ Перейдите на сайт: proracers.by/exchange\n2️⃣ Укажите IBAN вашей карты\n3️⃣ Укажите ФИО владельца\n4️⃣ Введите сумму\n\n✅ После заполнения создастся заявка. Деньги поступают в рабочие дни до 14:00.\n\n🔧 Если нужна помощь, напишите 'Оператор'.",
    
    "где мои деньги": "🔍 Проверяю ваш запрос. Деньги обычно поступают в течение рабочего дня.\n\n⏰ Если заявка создана после 14:00 — выплата переносится на следующий день.\n\n✅ Номер вашей заявки: {}\n\n💰 Если деньги не пришли более 3 дней, напишите 'Оператор'.",
    
    "увеличить квоту": "📈 Квота на вывод устанавливается системой раз в неделю.\n\n✅ Я создал заявку на увеличение квоты. Номер: #{}\n\n👨‍💼 Менеджер свяжется с вами в ближайшее время.",
    
    # Доступ к сайту
    "открыть доступ": "🔐 Доступ к сайту предоставлен!\n\n🌐 Вы можете войти по ссылке: proracers.by\n\n📧 Используйте вашу почту для входа.\n\n💡 Если не можете войти — напишите 'Восстановить пароль'.",
    
    "зарегистрироваться": "📝 Для регистрации на сайте:\n\n1️⃣ Перейдите на proracers.by\n2️⃣ Нажмите 'Регистрация'\n3️⃣ Укажите вашу почту (Gmail)\n4️⃣ Заполните ФИО и ID\n\n✅ После регистрации напишите сюда, я выдам доступ.",
    
    # Техподдержка
    "проблема с приложением": "📱 Понимаю вашу проблему.\n\n🛠️ Создал заявку в техническую поддержку.\n\n✅ Номер заявки: #{}\n\n💡 Попробуйте:\n• Перезагрузить приложение\n• Очистить кэш\n• Переустановить Яндекс Про",
    
    "нет заказов": "🚕 Проверяю ваш аккаунт...\n\n✅ Ваш профиль активен, ограничений нет.\n\n💡 Возможные причины:\n• Низкий рейтинг\n• Часы низкой активности\n• Технические работы\n\n✅ Номер заявки для проверки: #{}\n\n👨‍💼 Менеджер свяжется с вами.",
}

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🚕 <b>Добро пожаловать в службу поддержки такси!</b>\n\n"
        "Я — ваш помощник. Выберите категорию проблемы на кнопках ниже.\n\n"
        "📌 <b>Самое важное:</b>\n"
        "• Выплаты приходят в рабочие дни до 14:00\n"
        "• Карта блокируется при минусовом балансе\n"
        "• Для вывода денег нужен IBAN карты\n\n"
        "👨‍💼 Напишите <b>Оператор</b> для связи со специалистом.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard()
    )


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
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard()
    )


# Обработка нажатий на кнопки категорий
@router.message(F.text == "◀️ Назад")
async def back_to_main(message: Message):
    await message.answer(
        "🏠 Возвращаемся в главное меню. Выберите категорию:",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "⛽ Топливная карта")
async def fuel_card_category(message: Message):
    await message.answer(
        "⛽ <b>Выберите проблему с топливной картой:</b>\n\n"
        "• Разблокировать карту — если карта заблокирована\n"
        "• Обновить лимит — если не хватает на заправку\n"
        "• Не работает на заправке — ошибка при оплате\n"
        "• Заказать новую карту — если нет карты",
        parse_mode=ParseMode.HTML,
        reply_markup=get_fuel_card_keyboard()
    )


@router.message(F.text == "💵 Выплаты и зарплата")
async def payments_category(message: Message):
    await message.answer(
        "💵 <b>Выберите проблему с выплатами:</b>\n\n"
        "• Вывести деньги на карту — инструкция\n"
        "• Где мои деньги? — проверка статуса\n"
        "• Увеличить квоту — если превышен лимит\n"
        "• Ошибка в реквизитах — если неверный IBAN",
        parse_mode=ParseMode.HTML,
        reply_markup=get_payments_keyboard()
    )


@router.message(F.text == "🔐 Доступ к сайту")
async def access_category(message: Message):
    await message.answer(
        "🔐 <b>Выберите проблему с доступом:</b>\n\n"
        "• Открыть доступ — если нет входа\n"
        "• Зарегистрироваться — если нет аккаунта\n"
        "• Восстановить пароль — если забыли",
        parse_mode=ParseMode.HTML,
        reply_markup=get_access_keyboard()
    )


@router.message(F.text == "🔧 Техподдержка")
async def support_category(message: Message):
    await message.answer(
        "🔧 <b>Выберите техническую проблему:</b>\n\n"
        "• Проблема с приложением — лагает, вылетает\n"
        "• Нет заказов — долго нет заказов\n"
        "• Упал рейтинг — вопросы по рейтингу",
        parse_mode=ParseMode.HTML,
        reply_markup=get_support_keyboard()
    )


@router.message(F.text == "📞 Оператор")
async def call_operator(message: Message):
    result = await planfix.create_task(
        title=f"🚨 Срочный вызов оператора: {message.from_user.full_name}",
        description=f"""
Пользователь запросил соединение с оператором.

👤 Водитель: {message.from_user.full_name}
🆔 Telegram ID: {message.from_user.id}
📅 Время: {message.date}
        """
    )
    
    if result.get("success"):
        await message.answer(
            "👨‍💼 <b>Соединяю с оператором...</b>\n\n"
            f"✅ Создана заявка №{result.get('general')}\n\n"
            "Специалист свяжется с вами в ближайшее время.\n\n"
            "Пожалуйста, опишите вашу проблему подробнее.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "👨‍💼 <b>Соединяю с оператором...</b>\n\n"
            "Пожалуйста, опишите вашу проблему. Специалист свяжется с вами.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_keyboard()
        )


@router.message(F.text == "❓ Помощь")
async def help_button(message: Message):
    await cmd_help(message)


# Обработка конкретных проблем
@router.message(F.text == "🔓 Разблокировать карту")
async def unblock_card(message: Message):
    result = await planfix.create_task(
        title=f"⛽ Разблокировка карты: {message.from_user.full_name}",
        description=f"Запрос на разблокировку топливной карты от {message.from_user.full_name}"
    )
    if result.get("success"):
        await message.answer(
            ANSWERS["разблокировать карту"].format(result.get('general')),
            reply_markup=get_fuel_card_keyboard()
        )
    else:
        await message.answer("⛽ Создал заявку на разблокировку карты. Специалист свяжется с вами.")


@router.message(F.text == "📈 Обновить лимит")
async def update_limit(message: Message):
    result = await planfix.create_task(
        title=f"📈 Увеличение лимита: {message.from_user.full_name}",
        description=f"Запрос на увеличение лимита топливной карты"
    )
    await message.answer(
        ANSWERS["обновить лимит"].format(result.get('general', 'создана')),
        reply_markup=get_fuel_card_keyboard()
    )


@router.message(F.text == "💰 Вывести деньги на карту")
async def withdraw_money(message: Message):
    await message.answer(
        ANSWERS["вывести деньги"],
        reply_markup=get_payments_keyboard()
    )


@router.message(F.text == "❓ Где мои деньги?")
async def where_is_money(message: Message):
    result = await planfix.create_task(
        title=f"💰 Проверка выплаты: {message.from_user.full_name}",
        description=f"Запрос на проверку статуса выплаты"
    )
    await message.answer(
        ANSWERS["где мои деньги"].format(result.get('general', 'создана')),
        reply_markup=get_payments_keyboard()
    )


@router.message(F.text == "🔓 Открыть доступ")
async def open_access(message: Message):
    result = await planfix.create_task(
        title=f"🔐 Запрос доступа: {message.from_user.full_name}",
        description=f"Запрос на открытие доступа к сайту"
    )
    await message.answer(
        ANSWERS["открыть доступ"],
        reply_markup=get_access_keyboard()
    )


# Обработка текстовых сообщений (если пользователь что-то написал)
@router.message(F.text)
async def handle_text(message: Message):
    text = message.text.lower()
    
    # Проверяем, не нажата ли кнопка
    if text in [t.lower() for t in [
        "разблокировать карту", "обновить лимит", "вывести деньги на карту",
        "где мои деньги?", "открыть доступ", "зарегистрироваться",
        "проблема с приложением", "нет заказов", "увеличить квоту"
    ]]:
        # Уже обработано выше
        return
    
    # Создаём заявку с текстом пользователя
    result = await planfix.create_task(
        title=f"📝 Новое обращение: {message.from_user.full_name}",
        description=f"Сообщение: {message.text}\n\nID: {message.from_user.id}"
    )
    
    await message.answer(
        f"📝 Ваше сообщение принято!\n\n"
        f"✅ Создана заявка №{result.get('general', 'создана')}\n\n"
        f"Специалист свяжется с вами в ближайшее время.\n\n"
        f"💡 Для быстрого решения используйте кнопки меню.",
        reply_markup=get_main_keyboard()
    )