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
from bot.handlers.registration import router as registration_router
from bot.handlers import support

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем бота
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Создаем диспетчер
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# 🔥 ВАЖНО: СНАЧАЛА ПОДКЛЮЧАЕМ РЕГИСТРАЦИЮ, ПОТОМ ИИ
dp.include_router(registration_router)  # ← РЕГИСТРАЦИЯ ПЕРВАЯ
dp.include_router(support.router)       # ← ИИ ВТОРОЙ

# Настройка вебхука
WEBHOOK_PATH = f"/webhook/{settings.BOT_TOKEN}"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "") + WEBHOOK_PATH


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook установлен на: {WEBHOOK_URL}")
    yield
    await bot.delete_webhook()
    logger.info("❌ Webhook удален")


app = FastAPI(lifespan=lifespan)


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    json_data = await request.json()
    update = Update.model_validate(json_data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"status": "ok"}


@app.get("/health")
async def health_check():
    return {"status": "alive", "service": "taxi-support-bot", "version": "2.0"}


@app.get("/")
async def root():
    return {
        "message": "Taxi Support Bot is running!",
        "version": "2.0",
        "status": "active"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)