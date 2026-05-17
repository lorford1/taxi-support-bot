from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_keyboard():
    """Главная клавиатура с категориями"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="⛽ Топливная карта"),
        KeyboardButton(text="💵 Выплаты и зарплата"),
        KeyboardButton(text="🔐 Доступ к сайту"),
        KeyboardButton(text="🔧 Техподдержка"),
        KeyboardButton(text="🆘 Оператор срочно"),
        KeyboardButton(text="📞 Оператор"),
        KeyboardButton(text="❓ Помощь")
    )
    builder.adjust(2)  # 2 кнопки в ряд
    return builder.as_markup(resize_keyboard=True)


def get_fuel_card_keyboard():
    """Клавиатура для топливной карты"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="🔓 Разблокировать карту"),
        KeyboardButton(text="📈 Обновить лимит"),
        KeyboardButton(text="⛽ Не работает на заправке"),
        KeyboardButton(text="🆕 Заказать новую карту"),
        KeyboardButton(text="◀️ Назад")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_payments_keyboard():
    """Клавиатура для выплат"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="💰 Вывести деньги на карту"),
        KeyboardButton(text="❓ Где мои деньги?"),
        KeyboardButton(text="📈 Увеличить квоту"),
        KeyboardButton(text="💳 Ошибка в реквизитах"),
        KeyboardButton(text="◀️ Назад")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_access_keyboard():
    """Клавиатура для доступа к сайту"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="🔓 Открыть доступ"),
        KeyboardButton(text="📝 Зарегистрироваться на сайте"),
        KeyboardButton(text="🔄 Восстановить пароль"),
        KeyboardButton(text="◀️ Назад")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_support_keyboard():
    """Клавиатура для техподдержки"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="📱 Проблема с приложением"),
        KeyboardButton(text="🚫 Нет заказов"),
        KeyboardButton(text="⭐ Упал рейтинг"),
        KeyboardButton(text="◀️ Назад")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)