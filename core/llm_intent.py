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
        if not driver_name:
            driver_name = self._extract_name_from_message(user_message)
        
        prompt = f"""Ты — AI-агент службы поддержки водителей такси.

ВАЖНО: Водителя зовут {driver_name}. Обращайся к нему по имени в ответе.

Проанализируй сообщение водителя и верни ТОЛЬКО JSON.

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
            
            # Если модель всё ещё использует "Александр" или фамилию, исправляем
            if driver_name and driver_name != "водитель":
                old_name_patterns = ["Александр", driver_name.split()[-1] if driver_name else ""]
                for old_name in old_name_patterns:
                    if old_name and result.get("response") and old_name in result["response"]:
                        result["response"] = result["response"].replace(old_name, driver_name)
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI ошибка: {e}")
            return {
                "category": "unknown",
                "problem": "Не удалось определить",
                "solution": "",
                "need_manager": True,
                "response": f"🔍 Уважаемый {driver_name}, не смог точно определить вашу проблему. Создам заявку для специалиста."
            }
    
    def _extract_name_from_message(self, message: str) -> str:
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
                    return name_parts[1]
        return "водитель"

llm_classifier = LLMIntentClassifier()