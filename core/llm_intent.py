import json
import logging
import re
from openai import AsyncOpenAI
from core.config import settings

logger = logging.getLogger(__name__)

with open("core/knowledge_base.txt", "r", encoding="utf-8") as f:
    KNOWLEDGE_BASE = f.read()


class LLMIntentClassifier:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "ft:gpt-4o-mini-2024-07-18:neiropark:taxi-support-v3:DgeTtJB7"
    
    async def classify(self, user_message: str, driver_name: str = None) -> dict:
        """
        Определяет проблему по тексту сообщения с помощью обученной модели
        """
        # Извлекаем имя из сообщения, если не передано
        if not driver_name:
            driver_name = self._extract_name_from_message(user_message)
        
        # Формируем имя в правильном падеже для обращения
        greeting = "Уважаемый водитель"
        if driver_name and driver_name != "водитель":
            greeting = f"Уважаемый {driver_name}"
        
        prompt = f"""Ты — AI-агент службы поддержки водителей такси.

ВАЖНО: Водителя зовут {driver_name}. Обращайся к нему по имени в ответе (используй {greeting} или просто имя).

Проанализируй сообщение водителя и верни ТОЛЬКО JSON (без пояснений, без ```json).

Формат ответа:
{{
    "category": "Выплаты | Топливная карта | Доступ к сайту | Техподдержка",
    "problem": "название проблемы",
    "solution": "текст решения",
    "need_manager": true или false,
    "response": "короткий ответ водителю (2-3 предложения, дружелюбно, с эмодзи). Обращайся к водителю по имени {driver_name}"
}}

Сообщение водителя: "{user_message}"
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"Ты эксперт службы поддержки такси. Водителя зовут {driver_name}. Всегда обращайся к нему по имени в ответах. Отвечай только JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            result = json.loads(content)
            
            # Если модель не использовала имя, подставляем его в ответ
            if driver_name and driver_name != "водитель":
                if result.get("response") and "Александр" in result["response"]:
                    result["response"] = result["response"].replace("Александр", driver_name)
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI ошибка: {e}")
            return {
                "category": "unknown",
                "problem": "Не удалось определить",
                "solution": "",
                "need_manager": True,
                "response": f"🔍 {greeting}, не смог точно определить вашу проблему. Создам заявку для специалиста."
            }
    
    def _extract_name_from_message(self, message: str) -> str:
        """Пытается извлечь имя из сообщения"""
        patterns = [
            r"меня зовут ([А-Я][а-я]+ [А-Я][а-я]+ [А-Я][а-я]+)",
            r"это ([А-Я][а-я]+ [А-Я][а-я]+ [А-Я][а-я]+)",
            r"водитель ([А-Я][а-я]+ [А-Я][а-я]+ [А-Я][а-я]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                name_parts = match.group(1).split()
                if len(name_parts) >= 2:
                    return name_parts[0]  # возвращаем имя
        return "водитель"

llm_classifier = LLMIntentClassifier()