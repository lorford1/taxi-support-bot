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
        """
        Определяет проблему по тексту сообщения с помощью GPT-4o-mini
        """
        prompt = f"""Ты — AI-агент службы поддержки водителей такси.

Вот наша база знаний (категория → проблема → решение):
{KNOWLEDGE_BASE}

Проанализируй сообщение водителя и верни ТОЛЬКО JSON (без пояснений, без ```json).

Формат ответа:
{{
    "category": "Выплаты | Топливная карта | Доступ к сайту",
    "problem": "название проблемы из базы знаний",
    "solution": "полный текст решения из базы знаний",
    "need_manager": true/false,
    "response": "короткий ответ водителю (2-3 предложения, дружелюбно, с эмодзи)"
}}

Сообщение водителя: "{user_message}"
"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты эксперт службы поддержки такси. Отвечай только JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Очищаем ответ от возможных маркеров кода
            content = response.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            result = json.loads(content)
            return result
            
        except Exception as e:
            logger.error(f"OpenAI ошибка: {e}")
            return {
                "category": "unknown",
                "problem": "Не удалось определить",
                "solution": "",
                "need_manager": True,
                "response": "🔍 Не смог точно определить вашу проблему. Создам заявку для специалиста."
            }

llm_classifier = LLMIntentClassifier()