import json
import logging
from openai import AsyncOpenAI
from core.config import settings

logger = logging.getLogger(__name__)

# Читаем базу знаний (оставляем для совместимости, но модель уже обучена)
with open("core/knowledge_base.txt", "r", encoding="utf-8") as f:
    KNOWLEDGE_BASE = f.read()


class LLMIntentClassifier:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        # Используем обученную модель
        self.model = "ft:gpt-4o-mini-2024-07-18:neiropark:taxi-support-v3:DgeTtJB7"
    
    async def classify(self, user_message: str) -> dict:
        """
        Определяет проблему по тексту сообщения с помощью обученной модели
        """
        prompt = f"""Ты — AI-агент службы поддержки водителей такси.

Проанализируй сообщение водителя и верни ТОЛЬКО JSON (без пояснений, без ```json).

Формат ответа:
{{
    "category": "Выплаты | Топливная карта | Доступ к сайту | Техподдержка",
    "problem": "название проблемы",
    "solution": "текст решения",
    "need_manager": true или false,
    "response": "короткий ответ водителю (2-3 предложения, дружелюбно, с эмодзи)"
}}

Сообщение водителя: "{user_message}"
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
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