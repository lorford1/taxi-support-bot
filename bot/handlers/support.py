from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

from core.llm_intent import llm_classifier
from core.planfix_client import planfix

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🚕 <b>Добро пожаловать в службу поддержки такси!</b>\n\n"
        "Я — AI-помощник на базе GPT-4o-mini. Напишите свою проблему, и я помогу.\n\n"
        "<b>Примеры:</b>\n"
        "• Куда делись деньги?\n"
        "• Карта заблокировалась на заправке\n"
        "• Не могу зайти в личный кабинет",
        parse_mode=ParseMode.HTML
    )

@router.message()
async def handle_message(message: Message):
    user_text = message.text
    user_name = message.from_user.full_name
    
    # Вызываем GPT для анализа
    result = await llm_classifier.classify(user_text)
    
    if result.get("need_manager"):
        # Создаём задачу в Planfix
        task_result = await planfix.create_task(
            title=f"[{result.get('category', 'Поддержка')}] {user_name}",
            description=f"""
Сообщение: {user_text}
Категория: {result.get('category')}
Проблема: {result.get('problem')}
Решение: {result.get('solution')}
            """
        )
        
        if task_result.get("success"):
            await message.answer(
                f"{result.get('response')}\n\n"
                f"✅ Создана заявка №{task_result.get('general')}"
            )
        else:
            await message.answer(result.get('response'))
    else:
        await message.answer(result.get('response'))