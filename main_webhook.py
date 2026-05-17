import logging
import os
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from fastapi import FastAPI, Request

from core.config import settings
from bot.handlers import support
from bot.handlers.registration import router as registration_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем бота ПРАВИЛЬНЫМ способом для aiogram 3.x
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Создаем диспетчер с хранилищем в памяти
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Подключаем роутеры с обработчиками команд
dp.include_router(support.router)
dp.include_router(registration_router)

# Настройка вебхука
WEBHOOK_PATH = f"/webhook/{settings.BOT_TOKEN}"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "") + WEBHOOK_PATH


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # При запуске - устанавливаем вебхук
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook установлен на: {WEBHOOK_URL}")
    yield
    # При остановке - удаляем вебхук
    await bot.delete_webhook()
    logger.info("❌ Webhook удален")


# Создаем FastAPI приложение
app = FastAPI(lifespan=lifespan)


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    """Эндпоинт для получения обновлений от Telegram"""
    json_data = await request.json()
    update = Update.model_validate(json_data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"status": "ok"}


@app.get("/health")
async def health_check():
    """Эндпоинт для проверки работоспособности"""
    return {"status": "alive", "service": "taxi-support-bot", "version": "2.0"}


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Taxi Support Bot is running!",
        "version": "2.0",
        "status": "active",
        "features": [
            "AI-powered support (GPT-4o-mini)",
            "Planfix integration",
            "Driver registration",
            "Urgent operator calls"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)