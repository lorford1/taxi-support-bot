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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Правильное создание бота для aiogram 3.x
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.include_router(support.router)

WEBHOOK_PATH = f"/webhook/8742752684:AAFzIdIvsYSaCE3he4vunLpxciqacLTFWjc"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "") + WEBHOOK_PATH


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook set to {WEBHOOK_URL}")
    yield
    await bot.delete_webhook()


app = FastAPI(lifespan=lifespan)


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    json_data = await request.json()
    update = Update.model_validate(json_data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "alive"}


@app.get("/")
async def root():
    return {"message": "Taxi Support Bot is running!"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
