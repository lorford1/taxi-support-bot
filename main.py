import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import settings
from bot.handlers import support

# Настройка логирования (чтобы видеть ошибки)
logging.basicConfig(level=logging.INFO)

async def main():
    # Создаем бота
    bot = Bot(token=settings.BOT_TOKEN)
    
    # Хранилище для состояний (пока в памяти)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Подключаем обработчики
    dp.include_router(support.router)
    
    # Запускаем бота
    print("🚀 Бот запущен! Напишите @ваш_бот_username в Telegram")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())