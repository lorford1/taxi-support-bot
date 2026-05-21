import json
import logging
import re
from openai import AsyncOpenAI
from core.config import settings

logger = logging.getLogger(__name__)


class LLMIntentClassifier:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.fine_tuned_model = "ft:gpt-4o-mini-2024-07-18:neiropark:taxi-support-v4:DhlqPAT7"
        self.fallback_model = "gpt-4o-mini"
    
    async def classify(self, user_message: str, driver_name: str = None) -> dict:
        if not driver_name:
            driver_name = self._extract_name_from_message(user_message)
        
        prompt = f"""Ты — AI-агент службы поддержки водителей такси.

ВАЖНО: Водителя зовут {driver_name}. Обращайся к нему по имени.

Проанализируй сообщение водителя и верни ТОЛЬКО JSON. ВЫБЕРИ ТОЛЬКО ОДНУ КАТЕГОРИЮ.

Категории (выбери ОДНУ):
- "Выплаты" — вопросы о деньгах, выводе средств, зарплате, квотах
- "Топливная карта" — блокировка, лимиты, заправка
- "Доступ к сайту" — регистрация, вход, права
- "Техподдержка" — приложение, заказы, рейтинг

Формат ответа:
{{
    "category": "Выплаты | Топливная карта | Доступ к сайту | Техподдержка",
    "problem": "название проблемы (кратко)",
    "solution": "текст решения (если есть)",
    "need_manager": true или false,
    "response": "ответ водителю (2-3 предложения, дружелюбно, с эмодзи). Обращайся к водителю по имени {driver_name}. НЕ ПИШИ КАТЕГОРИЮ В ОТВЕТЕ."
}}

Сообщение водителя: "{user_message}"
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.fine_tuned_model,
                messages=[
                    {"role": "system", "content": f"Ты эксперт службы поддержки такси. Водителя зовут {driver_name}. Отвечай только JSON. ВСЕГДА выбирай ТОЛЬКО ОДНУ категорию из списка."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            result = json.loads(content)
            
            # Проверяем, не содержит ли ответ двух категорий
            if "|" in result.get("category", ""):
                result["category"] = result["category"].split("|")[0].strip()
            
            if result.get("category") == "unknown" or result.get("need_manager") is None:
                return await self._fallback_classify(user_message, driver_name)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return await self._fallback_classify(user_message, driver_name)
    
    async def _fallback_classify(self, user_message: str, driver_name: str) -> dict:
        """Запасной вариант с обычной GPT-4o-mini"""
        prompt = f"""Ты — AI-агент службы поддержки водителей такси.

Водителя зовут {driver_name}. Выбери ТОЛЬКО ОДНУ категорию.

Категории: Выплаты, Топливная карта, Доступ к сайту, Техподдержка.

Верни ТОЛЬКО JSON:
{{
    "category": "категория",
    "problem": "проблема",
    "solution": "решение",
    "need_manager": true,
    "response": "ответ водителю по имени {driver_name}"
}}

Сообщение: "{user_message}"
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.fallback_model,
                messages=[
                    {"role": "system", "content": "Ты эксперт. Отвечай только JSON. Выбирай одну категорию."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            content = response.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            return {
                "category": "unknown",
                "problem": "Не удалось определить",
                "solution": "",
                "need_manager": True,
                "response": f"🔍 Уважаемый {driver_name}, создам заявку для специалиста."
            }
    
    def _extract_name_from_message(self, message: str) -> str:
        name_match = re.search(r'([А-Я][а-я]+)\s+([А-Я][а-я]+)', message)
        if name_match:
            return name_match.group(1)
        return "водитель"

llm_classifier = LLMIntentClassifier()