import asyncio
import logging
import os
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from fastapi import FastAPI, Request

from core.config import settings
from core.intent_classifier import classifier
from core.planfix_client import planfix
from bot.handlers import support

logging.basicConfig(level=logging.INFO)

# Создаем бота и диспетчер
bot = Bot(token=settings.BOT_TOKEN, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Подключаем роутеры
dp.include_router(support.router)

# Настройка вебхука
WEBHOOK_PATH = f"/webhook/{settings.BOT_TOKEN}"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "") + WEBHOOK_PATH


@asynccontextmanager
async def lifespan(app: FastAPI):
    # При запуске сервера — устанавливаем вебхук
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set to {WEBHOOK_URL}")
    yield
    # При остановке — удаляем вебхук
    await bot.delete_webhook()


app = FastAPI(lifespan=lifespan)


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    """Принимает обновления от Telegram"""
    json_data = await request.json()
    update = Update.model_validate(json_data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "alive"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))