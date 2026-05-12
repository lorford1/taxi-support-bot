from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from core.intent_classifier import classifier

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🚕 <b>Добро пожаловать в службу поддержки такси!</b>\n\n"
        "Я помогаю водителям. Напишите ваш вопрос, и я постараюсь помочь.\n\n"
        "<b>Примеры вопросов:</b>\n"
        "• Куда делись деньги?\n"
        "• Топливная карта не работает\n"
        "• Нет доступа к сайту\n\n"
        "Если бот не поможет, напишите <b>Оператор</b>",
        parse_mode="HTML"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 <b>Команды:</b>\n"
        "/start - начать работу\n"
        "/help - эта справка\n\n"
        "<b>Или просто напишите вашу проблему:</b>\n"
        "• Деньги не пришли\n"
        "• Карта заблокирована\n"
        "• Нет доступа",
        parse_mode="HTML"
    )

@router.message()
async def handle_message(message: Message):
    """Обработка любого сообщения"""
    user_text = message.text
    
    # Проверка на вызов оператора
    if user_text.lower() in ["оператор", "менеджер", "человек", "помощь"]:
        await message.answer(
            "👨‍💼 Сейчас соединю вас с оператором.\n"
            "Пожалуйста, опишите вашу проблему, и специалист свяжется с вами."
        )
        return
    
    # Анализируем через классификатор
    result = classifier.classify(user_text)
    
    if result["found"]:
        # Отправляем решение
        response = f"{result['solution']}\n"
        if result["need_manager"]:
            response += "\n👨‍💼 Для решения этой проблемы потребуется помощь менеджера. Я создал заявку, ответим в ближайшее время."
        
        await message.answer(response)
    else:
        # Не распознали проблему
        await message.answer(
            "🤔 Я не совсем понял вашу проблему.\n\n"
            "Выберите категорию:\n"
            "• Выплаты / деньги\n"
            "• Топливная карта\n"
            "• Доступ к сайту\n\n"
            "Или напишите 'Оператор' для связи со специалистом."
        )