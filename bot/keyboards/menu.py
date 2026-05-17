from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_registered_keyboard():
    """Клавиатура для зарегистрированного пользователя"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="❓ Помощь"),
        KeyboardButton(text="📞 Оператор")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_unregistered_keyboard():
    """Клавиатура для незарегистрированного пользователя"""
    buttons = [[KeyboardButton(text="📝 Зарегистрироваться")]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_main_keyboard():
    """Алиас для совместимости со старым кодом"""
    return get_registered_keyboard()