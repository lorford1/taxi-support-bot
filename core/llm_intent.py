import json
import logging
import re
from openai import AsyncOpenAI
from core.config import settings

logger = logging.getLogger(__name__)

# База знаний (оставляем для fallback)
with open("core/knowledge_base.txt", "r", encoding="utf-8") as f:
    KNOWLEDGE_BASE = f.read()


class LLMIntentClassifier:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        # Обученная модель v4 (3652 примера)
        self.fine_tuned_model = "ft:gpt-4o-mini-2024-07-18:neiropark:taxi-support-v4:DhlqPAT7"
        self.fallback_model = "gpt-4o-mini"
    
    async def classify(self, user_message: str, driver_name: str = None) -> dict:
        """
        Определяет проблему по тексту сообщения с помощью обученной модели
        """
        if not driver_name:
            driver_name = self._extract_name_from_message(user_message)
        
        prompt = f"""Ты — AI-агент службы поддержки водителей такси.

ВАЖНО: Водителя зовут {driver_name}. Обращайся к нему по имени в ответе.

Проанализируй сообщение водителя и верни ТОЛЬКО JSON (без пояснений, без ```json).

Категории (выбери ТОЛЬКО ОДНУ):
- "Выплаты" — вопросы о деньгах, выводе средств, зарплате, квотах, балансе
- "Топливная карта" — блокировка, лимиты, заправка, разблокировка
- "Доступ к сайту" — регистрация, вход, права, доступ к сайту
- "Техподдержка" — приложение, заказы, рейтинг, проблемы с Яндекс Про

Формат ответа:
{{
    "category": "Выплаты | Топливная карта | Доступ к сайту | Техподдержка",
    "problem": "краткое название проблемы (2-5 слов)",
    "solution": "текст решения проблемы (если есть)",
    "need_manager": true или false,
    "response": "короткий ответ водителю (2-3 предложения, дружелюбно, с эмодзи). Обращайся к водителю по имени {driver_name}. НЕ ПИШИ КАТЕГОРИЮ В ОТВЕТЕ."
}}

Сообщение водителя: "{user_message}"
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.fine_tuned_model,
                messages=[
                    {"role": "system", "content": f"Ты эксперт службы поддержки такси. Водителя зовут {driver_name}. Всегда обращайся к нему по имени. Отвечай ТОЛЬКО JSON, выбирай ОДНУ категорию."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            result = json.loads(content)
            
            # Проверяем, не содержит ли категория двух значений
            if "|" in result.get("category", ""):
                result["category"] = result["category"].split("|")[0].strip()
            
            # Если модель не распознала, используем fallback
            if result.get("category") == "unknown" or result.get("need_manager") is None:
                logger.info(f"Обученная модель не распознала, используем fallback")
                return await self._fallback_classify(user_message, driver_name)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка обученной модели: {e}")
            return await self._fallback_classify(user_message, driver_name)
    
    async def _fallback_classify(self, user_message: str, driver_name: str) -> dict:
        """Запасной вариант с обычной GPT-4o-mini и полной базой знаний"""
        prompt = f"""Ты — AI-агент службы поддержки водителей такси.

Вот наша база знаний:
{KNOWLEDGE_BASE}

ВАЖНО: Водителя зовут {driver_name}. Обращайся к нему по имени.

Проанализируй сообщение водителя и верни ТОЛЬКО JSON.

Категории (выбери ТОЛЬКО ОДНУ):
- "Выплаты"
- "Топливная карта"
- "Доступ к сайту"
- "Техподдержка"

Формат ответа:
{{
    "category": "категория",
    "problem": "название проблемы",
    "solution": "текст решения из базы знаний",
    "need_manager": true или false,
    "response": "короткий ответ водителю (2-3 предложения, дружелюбно, с эмодзи). Обращайся к водителю по имени {driver_name}"
}}

Сообщение водителя: "{user_message}"
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.fallback_model,
                messages=[
                    {"role": "system", "content": f"Ты эксперт службы поддержки такси. Водителя зовут {driver_name}. Отвечай ТОЛЬКО JSON, выбирай ОДНУ категорию."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            result = json.loads(content)
            return result
            
        except Exception as e:
            logger.error(f"Ошибка fallback модели: {e}")
            return {
                "category": "unknown",
                "problem": "Не удалось определить",
                "solution": "",
                "need_manager": True,
                "response": f"🔍 Уважаемый {driver_name}, не смог точно определить вашу проблему. Создам заявку для специалиста."
            }
    
    def _extract_name_from_message(self, message: str) -> str:
        """Извлекает имя из сообщения"""
        # Пробуем найти ФИО в формате "Иванов Иван Иванович"
        patterns = [
            r"(?:меня зовут|это|водитель)\s+([А-Я][а-я]+)\s+([А-Я][а-я]+)\s+([А-Я][а-я]+)",
            r"(?:меня зовут|это|водитель)\s+([А-Я][а-я]+)\s+([А-Я][а-я]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(2) if len(match.groups()) >= 2 else match.group(1)
        
        # Если не найдено, возвращаем "водитель"
        return "водитель"


# Создаём глобальный экземпляр
llm_classifier = LLMIntentClassifier()