import json
import logging
from openai import AsyncOpenAI
from core.config import settings

logger = logging.getLogger(__name__)

# Читаем базу знаний
with open("core/knowledge_base.txt", "r", encoding="utf-8") as f:
    KNOWLEDGE_BASE = f.read()


class LLMIntentClassifier:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def classify(self, user_message: str) -> dict:
        prompt = f"""Ты — AI-агент службы поддержки водителей такси.

Вот наша база знаний:
{KNOWLEDGE_BASE}

Верни ТОЛЬКО JSON (без пояснений):
{{
    "category": "Выплаты | Топливная карта | Доступ к сайту",
    "problem": "название проблемы",
    "solution": "решение из базы знаний",
    "need_manager": false,
    "response": "короткий ответ водителю"
}}

Сообщение: "{user_message}"
"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            logger.error(f"OpenAI ошибка: {e}")
            return {
                "category": "unknown",
                "problem": "Не удалось определить",
                "solution": "",
                "need_manager": True,
                "response": "Не смог распознать проблему. Создам заявку специалисту."
            }

llm_classifier = LLMIntentClassifier()