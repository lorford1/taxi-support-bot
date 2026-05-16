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


# ============ КЛАВИАТУРЫ ДЛЯ РЕГИСТРАЦИИ ============

def get_registered_keyboard():
    from bot.handlers.registration import get_registered_keyboard as grk
    return grk()


def get_unregistered_keyboard():
    from bot.handlers.registration import get_unregistered_keyboard as guk
    return guk()


# ============ БАЗА ОТВЕТОВ ============

ANSWERS = {
    "вывести деньги": "💰 <b>Инструкция по выводу денег на карту</b>\n\n"
                      "1️⃣ Перейдите на сайт: <code>https://proracers.by/exchange</code>\n"
                      "2️⃣ Укажите сумму вывода\n"
                      "3️⃣ Введите IBAN вашей карты\n"
                      "4️⃣ Укажите ФИО владельца карты\n\n"
                      "⏰ Деньги поступают в рабочие дни до 14:00\n"
                      "📧 На почту придёт подтверждение запроса",
    
    "где мои деньги": "🔍 <b>Проверка статуса выплаты</b>\n\n"
                      "✅ Я создал заявку на проверку. Номер: #{}\n\n"
                      "⏰ Обычно деньги поступают в течение рабочего дня.\n"
                      "📞 Если прошло более 3 дней — напишите 'Оператор'.",
    
    "увеличить квоту": "📈 <b>Увеличение квоты на вывод</b>\n\n"
                       "✅ Создана заявка на увеличение квоты. Номер: #{}\n\n"
                       "👨‍💼 Менеджер свяжется с вами для уточнения деталей.\n"
                       "📊 Квота обновляется раз в неделю.",
    
    "ошибка реквизиты": "💳 <b>Ошибка в реквизитах карты</b>\n\n"
                        "Проверьте правильность ввода:\n"
                        "• IBAN должен содержать только буквы и цифры\n"
                        "• ФИО должно быть на русском языке\n"
                        "• Номер карты должен быть активным\n\n"
                        "✅ Создана заявка на проверку. Номер: #{}",
    
    "открыть доступ": "🔐 <b>Доступ к сайту</b>\n\n"
                      "✅ Доступ предоставлен!\n\n"
                      "🌐 Войдите на сайт: <code>https://proracers.by</code>\n"
                      "📧 Используйте вашу почту для входа.\n\n"
                      "💡 Если не можете войти — напишите 'Восстановить пароль'.",
    
    "восстановить пароль": "🔄 <b>Восстановление пароля</b>\n\n"
                           "1️⃣ Перейдите на страницу входа: <code>https://proracers.by</code>\n"
                           "2️⃣ Нажмите 'Забыли пароль?'\n"
                           "3️⃣ Введите вашу почту\n"
                           "4️⃣ Следуйте инструкциям в письме\n\n"
                           "✅ Если не приходит письмо — напишите 'Оператор'.",
    
    "проблема приложение": "📱 <b>Проблема с приложением Яндекс Про</b>\n\n"
                          "✅ Создана заявка в техподдержку. Номер: #{}\n\n"
                          "💡 Попробуйте:\n"
                          "• Перезагрузить приложение\n"
                          "• Очистить кэш\n"
                          "• Переустановить приложение\n\n"
                          "🛠️ Специалист проверит ваш аккаунт.",
    
    "нет заказов": "🚕 <b>Нет заказов</b>\n\n"
                   "✅ Создана заявка на проверку. Номер: #{}\n\n"
                   "💡 Возможные причины:\n"
                   "• Низкий рейтинг (ниже 4.5)\n"
                   "• Часы низкой активности\n"
                   "• Технические работы\n\n"
                   "👨‍💼 Менеджер свяжется с вами.",
    
    "упал рейтинг": "⭐ <b>Вопросы по рейтингу</b>\n\n"
                    "✅ Создана заявка для анализа. Номер: #{}\n\n"
                    "💡 Рейтинг зависит от:\n"
                    "• Оценок пассажиров\n"
                    "• Процента принятых заказов\n"
                    "• Отмен и опозданий\n\n"
                    "👨‍💼 Специалист даст рекомендации.",
}


# ============ ОСНОВНЫЕ КОМАНДЫ ============

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    user = user_storage.get_user(telegram_id)
    
    if user:
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
        "2️⃣ Выберите конкретую проблему\n"
        "3️⃣ Бот создаст заявку и даст ответ\n\n"
        "<b>Команды:</b>\n"
        "/start — главное меню\n"
        "/help — эта справка\n\n"
        "📞 <b>Оператор</b> — связь с живым специалистом",
        parse_mode="HTML"
    )


# ============ НАВИГАЦИЯ ============

@router.message(F.text == "◀️ Назад")
async def back_to_main(message: Message):
    await message.answer(
        "🏠 <b>Главное меню</b>\n\nВыберите категорию:",
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
    
    result = await planfix.create_task(
        title=f"🚨 Срочный вызов оператора: {driver_name}",
        description=f"""
Пользователь запросил соединение с оператором.

👤 Водитель: {driver_name}
🆔 ID: {driver_id}
📅 Время: {message.date}
🆔 Telegram ID: {message.from_user.id}
👥 Username: @{message.from_user.username or 'не указан'}
        """
    )
    
    await status_msg.delete()
    
    if result.get("success"):
        await message.answer(
            f"👨‍💼 <b>Соединяю с оператором...</b>\n\n"
            f"✅ Создана заявка №{result.get('general')}\n\n"
            f"Специалист свяжется с вами в ближайшее время.\n\n"
            f"Пожалуйста, опишите вашу проблему подробнее.",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"❌ <b>Ошибка при создании заявки!</b>\n\n"
            f"📋 Ошибка: {result.get('error')}\n\n"
            f"Пожалуйста, обратитесь к оператору напрямую.",
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
        "• 🆕 Заказать новую карту",
        parse_mode="HTML",
        reply_markup=get_fuel_card_keyboard()
    )


@router.message(F.text == "🔓 Разблокировать карту")
async def unblock_card(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    result = await planfix.create_task(
        title=f"⛽ Разблокировка карты: {driver_name} (ID: {driver_id})",
        description=f"""
Запрос на разблокировку топливной карты

👤 Водитель: {driver_name}
🆔 ID: {driver_id}
📅 Время: {message.date}
📱 Telegram ID: {message.from_user.id}
        """
    )
    
    await status_msg.delete()
    
    if result.get("success"):
        await message.answer(
            f"🔓 <b>Хорошо, {driver_name}!</b>\n\n"
            f"✅ Заявка №{result.get('general')} создана в Planfix!\n\n"
            f"📅 Задача появится в Планировщике.\n\n"
            f"👨‍💼 Специалист свяжется с вами.",
            parse_mode="HTML",
            reply_markup=get_fuel_card_keyboard()
        )
    else:
        error_text = result.get('error', 'Неизвестная ошибка')
        await message.answer(
            f"❌ <b>Ошибка при создании заявки!</b>\n\n"
            f"📋 Текст ошибки:\n<code>{error_text}</code>\n\n"
            f"Пожалуйста, обратитесь к оператору.",
            parse_mode="HTML",
            reply_markup=get_fuel_card_keyboard()
        )


@router.message(F.text == "📈 Обновить лимит")
async def update_limit(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    result = await planfix.create_task(
        title=f"📈 Обновление лимита: {driver_name}",
        description=f"Запрос на обновление лимита топливной карты\nВодитель: {driver_name}"
    )
    
    await status_msg.delete()
    
    if result.get("success"):
        await message.answer(
            f"📈 <b>Хорошо, {driver_name}!</b>\n\n"
            f"✅ Создана заявка на обновление лимита. Номер: #{result.get('general')}\n\n"
            f"⛽ Лимит будет обновлён в ближайшее время.",
            parse_mode="HTML",
            reply_markup=get_fuel_card_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка: {result.get('error')}\nОбратитесь к оператору.",
            reply_markup=get_fuel_card_keyboard()
        )


@router.message(F.text == "⛽ Не работает на заправке")
async def card_not_working(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    result = await planfix.create_task(
        title=f"⛽ Проблема на заправке: {driver_name}",
        description=f"Водитель сообщает, что карта не работает на заправке\nВодитель: {driver_name}"
    )
    
    await status_msg.delete()
    
    if result.get("success"):
        await message.answer(
            f"⛽ <b>Понимаю вашу ситуацию, {driver_name}!</b>\n\n"
            f"✅ Создана заявка в техподдержку. Номер: #{result.get('general')}\n\n"
            f"🛠️ Специалист проверит статус вашей карты.\n\n"
            f"💡 Попробуйте перезагрузить приложение BNCard.",
            parse_mode="HTML",
            reply_markup=get_fuel_card_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка: {result.get('error')}",
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
        f"💡 Если SMS не пришло в течение часа — напишите 'Оператор'.",
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
        "• 💳 Ошибка в реквизитах",
        parse_mode="HTML",
        reply_markup=get_payments_keyboard()
    )


@router.message(F.text == "💰 Вывести деньги на карту")
async def withdraw_money(message: Message):
    await message.answer(
        ANSWERS["вывести деньги"],
        parse_mode="HTML",
        reply_markup=get_payments_keyboard(),
        disable_web_page_preview=True
    )


@router.message(F.text == "❓ Где мои деньги?")
async def where_is_money(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    result = await planfix.create_task(
        title=f"💰 Проверка выплаты: {driver_name}",
        description=f"Запрос на проверку статуса выплаты\nВодитель: {driver_name}"
    )
    
    await status_msg.delete()
    
    if result.get("success"):
        await message.answer(
            ANSWERS["где мои деньги"].format(result.get('general', 'создана')),
            parse_mode="HTML",
            reply_markup=get_payments_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка: {result.get('error')}",
            reply_markup=get_payments_keyboard()
        )


@router.message(F.text == "📈 Увеличить квоту")
async def increase_quota(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    result = await planfix.create_task(
        title=f"📈 Увеличение квоты: {driver_name}",
        description=f"Запрос на увеличение квоты вывода средств\nВодитель: {driver_name}"
    )
    
    await status_msg.delete()
    
    if result.get("success"):
        await message.answer(
            ANSWERS["увеличить квоту"].format(result.get('general', 'создана')),
            parse_mode="HTML",
            reply_markup=get_payments_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка: {result.get('error')}",
            reply_markup=get_payments_keyboard()
        )


@router.message(F.text == "💳 Ошибка в реквизитах")
async def wrong_details(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    result = await planfix.create_task(
        title=f"💳 Ошибка в реквизитах: {driver_name}",
        description=f"Запрос на проверку реквизитов карты\nВодитель: {driver_name}"
    )
    
    await status_msg.delete()
    
    if result.get("success"):
        await message.answer(
            ANSWERS["ошибка реквизиты"].format(result.get('general', 'создана')),
            parse_mode="HTML",
            reply_markup=get_payments_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка: {result.get('error')}",
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
        "• 🔄 Восстановить пароль",
        parse_mode="HTML",
        reply_markup=get_access_keyboard()
    )


@router.message(F.text == "🔓 Открыть доступ")
async def open_access(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    driver_id = user_data.get('driver_id', 'не указан')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    result = await planfix.create_task(
        title=f"🔐 Запрос доступа: {driver_name} (ID: {driver_id})",
        description=f"Запрос на открытие доступа к сайту\nВодитель: {driver_name}\nID: {driver_id}"
    )
    
    await status_msg.delete()
    
    if result.get("success"):
        await message.answer(
            ANSWERS["открыть доступ"],
            parse_mode="HTML",
            reply_markup=get_access_keyboard(),
            disable_web_page_preview=True
        )
    else:
        await message.answer(
            f"❌ Ошибка: {result.get('error')}",
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
        ANSWERS["восстановить пароль"],
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
        "• ⭐ Упал рейтинг",
        parse_mode="HTML",
        reply_markup=get_support_keyboard()
    )


@router.message(F.text == "📱 Проблема с приложением")
async def app_problem(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    result = await planfix.create_task(
        title=f"📱 Проблема с приложением: {driver_name}",
        description=f"Запрос о проблеме с приложением Яндекс Про\nВодитель: {driver_name}"
    )
    
    await status_msg.delete()
    
    if result.get("success"):
        await message.answer(
            ANSWERS["проблема приложение"].format(result.get('general', 'создана')),
            parse_mode="HTML",
            reply_markup=get_support_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка: {result.get('error')}",
            reply_markup=get_support_keyboard()
        )


@router.message(F.text == "🚫 Нет заказов")
async def no_orders(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    result = await planfix.create_task(
        title=f"🚫 Нет заказов: {driver_name}",
        description=f"Запрос о проблеме отсутствия заказов\nВодитель: {driver_name}"
    )
    
    await status_msg.delete()
    
    if result.get("success"):
        await message.answer(
            ANSWERS["нет заказов"].format(result.get('general', 'создана')),
            parse_mode="HTML",
            reply_markup=get_support_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка: {result.get('error')}",
            reply_markup=get_support_keyboard()
        )


@router.message(F.text == "⭐ Упал рейтинг")
async def rating_dropped(message: Message, state: FSMContext):
    user_data = await state.get_data()
    driver_name = user_data.get('fullname', 'водитель')
    
    status_msg = await message.answer("🔄 Отправляю запрос в Planfix...")
    
    result = await planfix.create_task(
        title=f"⭐ Вопрос по рейтингу: {driver_name}",
        description=f"Запрос о падении рейтинга водителя\nВодитель: {driver_name}"
    )
    
    await status_msg.delete()
    
    if result.get("success"):
        await message.answer(
            ANSWERS["упал рейтинг"].format(result.get('general', 'создана')),
            parse_mode="HTML",
            reply_markup=get_support_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка: {result.get('error')}",
            reply_markup=get_support_keyboard()
        )